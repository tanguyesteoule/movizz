import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from .views import Game, Question, Movie, Answer, QuestionImage, Screenshot, AnswerImage
from django.db.models import F
import numpy as np

#######################
# Room play
#######################

class GameMasterConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.game_name = self.scope['url_route']['kwargs']['game_name']
        self.room_group_name = 'chat_%s' % self.game_name
        self.dict_user = self.scope["session"]["dict_user"]
        self.game_mode = self.scope["session"]["game_mode"]
        self.game_mode_debrief = self.scope["session"]["game_mode_debrief"]
        # self.mode = 'chill' 'timer'
        self.list_id = list(self.dict_user.keys())
        # self.current_q = 0
        self.dict_score = {user_id:0 for user_id in self.list_id}
        self.dict_score_current = {user_id:0 for user_id in self.list_id}
        self.dict_current_answer = {user_id:0 for user_id in self.list_id}
        self.task_sleep_reveal = False

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.init_game()
        if self.game_mode != 'chill':
            # await self.next_question()
            # asyncio.create_task(self.next_question)
            self.task_sleep_reveal = asyncio.ensure_future(self.next_reveal())
            # self.task_sleep_reveal = asyncio.create_task(self.next_reveal())

    async def init_game(self):
        self.game, self.questions, self.nb_questions, self.current_q = await self.data_init()

    @database_sync_to_async
    def data_init(self):
        game = Game.objects.get(name=self.game_name)
        questions = Question.objects.filter(game_id=game.id).order_by('id')
        nb_questions = game.nb_q
        current_q = game.current_q
        return game, questions, nb_questions, current_q

    @database_sync_to_async
    def get_data(self, current_q):
        # Pas sûr que ça doit un vrai accès en base ? sync vraiment nécessaire ?
        q = self.questions[current_q]

        context = {
            'q_id':q.id,
            'movie1_id':q.movie1.id,
            'movie2_id': q.movie2.id,
            'movie3_id': q.movie3.id,
            'movie1_name': q.movie1.name,
            'movie2_name': q.movie2.name,
            'movie3_name': q.movie3.name,
            'movie1_url': str(q.movie1.image),
            'movie2_url': str(q.movie2.image),
            'movie3_url': str(q.movie3.image),
            'quote_text': q.quote.quote_text,
            'list_user_id': self.list_id,
            'current_answer': json.dumps(self.dict_current_answer),
            'dict_user': json.dumps(self.dict_user)

        }
        return context

    @database_sync_to_async
    def incr_current_q(self):
        Game.objects.filter(id=self.game.id).update(current_q=F("current_q") + 1)

    @database_sync_to_async
    def end_current_q(self):
        Game.objects.filter(id=self.game.id).update(current_q=-1)

    @database_sync_to_async
    def compute_score(self, i):
        q = self.questions[i]
        for user_id in self.list_id:
            count = Answer.objects.filter(question_id=q.id, movie_prop_id=q.movie_guessed.id, user_id=user_id).count()
            self.dict_score[user_id] += count
        self.dict_score = dict(sorted(self.dict_score.items(), key=lambda item: item[1], reverse=True))

    async def next_reveal(self):
        # Attend Xs et ordonne de reveal answer
        # 0.5 to take into account delay
        time_step = int(self.game_mode) + 0.5
        await asyncio.sleep(time_step)

        await self.send_reveal()

        # Si mode debrief timer, on attend et envoie la prochaine question
        if self.game_mode_debrief != 'chill':
            time_step_debrief = int(self.game_mode_debrief) + 0.5
            await asyncio.sleep(time_step_debrief)
            await self.next_question_chill()

        # for i in range(1, self.nb_questions):
        #     time_step = int(self.game_mode)
        #     await asyncio.sleep(time_step)
        #
        #     self.dict_current_answer = {user_id: 0 for user_id in self.list_id}
        #     context = await self.get_data(i)
        #     await self.compute_score(i - 1)
        #     context['type'] = 'user_message'
        #     context['code'] = 'idle'
        #     context['dict_score'] = json.dumps(self.dict_score)
        #
        #     await self.incr_current_q()
        #
        #     await self.channel_layer.group_send(self.room_group_name, context)
        #
        # await asyncio.sleep(time_step)
        # await self.end_current_q()
        # await self.disconnect('normal')

    async def next_question_chill(self):

        if self.current_q < self.nb_questions - 1:
            self.dict_current_answer = {user_id: 0 for user_id in self.list_id}
            self.dict_score_current = {u_id:0 for u_id in self.dict_score.keys()}
            context = await self.get_data(self.current_q+1)
            await self.compute_score(self.current_q)
            context['type'] = 'user_message'
            context['code'] = 'idle'
            context['dict_score'] = json.dumps(self.dict_score)


            await self.incr_current_q()
            self.current_q += 1
            await self.channel_layer.group_send(self.room_group_name, context)
        else:
            await self.end_current_q()
            await self.disconnect('normal')

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message == 'next':
            # Send message to room group
            if self.task_sleep_reveal != False:
                self.task_sleep_reveal.cancel()
            await self.next_question_chill()
        elif message == 'sleep_reveal':
            # await self.next_reveal()
            self.task_sleep_reveal = asyncio.ensure_future(self.next_reveal())


    @database_sync_to_async
    def change_host(self, new_host):
        Game.objects.filter(id=self.game.id).update(host=new_host)

    async def disconnect(self, close_code):
        # self.close()
        # Normal end
        if close_code == 'normal':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_message',
                    'code': 'end'
                }
            )
        else:
            # Si le game master quitte la page, la partie est arrêtée et on change d'host
            # list_new_host = [u_id for u_id in self.list_id if u_id != self.user_id]
            # if len(list_new_host) != 0:
            #     new_host = list_new_host[0]
            #     new_dict_user = {key: self.dict_user[key] for key in list_new_host}
        
            #     await self.change_host(new_host)

            # Envoie un message pour dire d'arrêter la partie
            context = {
                'type': 'interruption',
                'code': 'interruption',
            }
            
            await self.channel_layer.group_send(self.room_group_name, context)

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    @database_sync_to_async
    def is_correct(self, i, movie_id):
        q = self.questions[i]
        if q.movie_guessed.id == int(movie_id):
            return 1
        else:
            return 0

    async def newanswer(self, event):
        if event['code'] == 'new_answer':
            
            ans = await self.is_correct(self.current_q, event['movie_id'])
            self.dict_score_current[event['user_id']] = ans
            self.dict_current_answer[event['user_id']] = 1
            context = {
                'type': 'newansweruser',
                'code': 'newanswer',
                'current_answer': json.dumps(self.dict_current_answer),
                'list_user_id': self.list_id,
                'dict_user': json.dumps(self.dict_user),
                'dict_score': json.dumps(self.dict_score)
            }
            await self.channel_layer.group_send(self.room_group_name, context)

            # TODO : Pour eviter les problèmes de concurrence entre next_reveal et ici
            if self.game_mode == 'chill' or self.game_mode_debrief == 'chill':
                # If everybody answered
                if sum(self.dict_current_answer.values()) == len(self.list_id):
                    if self.task_sleep_reveal != False:
                        self.task_sleep_reveal.cancel()

                    await self.send_reveal()
                    
                    if self.game_mode_debrief != 'chill':
                        time_step_debrief = int(self.game_mode_debrief) + 0.5
                        await asyncio.sleep(time_step_debrief)
                        await self.next_question_chill()


    async def send_reveal(self):
        context = {
            'type': 'revealanswer',
            'code': 'revealanswer',
            'dict_score_current': json.dumps(self.dict_score_current),
            'list_user_id': self.list_id,
            'dict_user': json.dumps(self.dict_user),
            'dict_score': json.dumps(self.dict_score)
        }
        await self.channel_layer.group_send(self.room_group_name, context)

    async def revealanswer(self, event):
        pass

    async def newansweruser(self, event):
        pass

    async def user_message(self, event):
        pass

    async def user_updateuser(self, event):
        pass

    async def interruption(self, event):
        pass


class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["session"]["user_id"]
        self.user_name = self.scope["session"]["user_name"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.game_name = self.scope['url_route']['kwargs']['game_name']
        self.room_group_name = 'chat_%s' % self.game_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def interruption(self, data):

        message = {'code': 'interruption'}
        # if data['new_host_id'] == self.user_id:
        #     message['is_new_host'] = '1'
        #     message['new_host_id'] = data['new_host_id']
        #     message['new_dict_user'] = data['new_dict_user']
        # else:
        #     message['is_new_host'] = '0'

        await self.send(text_data=json.dumps(message))

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message == 'new_answer':
            # Send message to room group
            context = {
                'type': 'newanswer',
                'code': 'new_answer',
                'user_id': self.user_id,
                'movie_id': text_data_json['movie_id']
            }
            await self.channel_layer.group_send(self.room_group_name, context)


    async def user_message(self, data):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(data))

    async def newansweruser(self, data):
        # Send message to WebSocket
        context = {'current_answer': data['current_answer'],
                   'list_user_id': data['list_user_id'],
                   'dict_user': data['dict_user'],
                   'dict_score': data['dict_score'],
                   }
        await self.send(text_data=json.dumps(context))

    async def revealanswer(self, data):
        context = {'code': 'reveal',
                   'dict_score_current': data['dict_score_current'],
                   'list_user_id': data['list_user_id'],
                   'dict_user': data['dict_user'],
                   'dict_score': data['dict_score'],
                   }
         
        await self.send(text_data=json.dumps(context))

    async def user_connection(self, event):
        pass

    async def newanswer(self, event):
        pass


#######################
# Game Image
#######################

class GameMasterConsumerImage(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.game_name = self.scope['url_route']['kwargs']['game_name']
        self.room_group_name = 'chat_%s' % self.game_name
        self.dict_user = self.scope["session"]["dict_user"]
        self.game_mode = self.scope["session"]["game_mode"]
        self.game_mode_debrief = self.scope["session"]["game_mode_debrief"]
        # self.mode = 'chill' 'timer'
        self.list_id = list(self.dict_user.keys())
        # self.current_q = 0
        self.dict_score = {user_id:0 for user_id in self.list_id}
        self.dict_score_current = {user_id:0 for user_id in self.list_id}
        self.dict_current_answer = {user_id:0 for user_id in self.list_id}
        self.task_sleep_reveal = False
        self.task_sleep_image = False
        self.current_q_image = 0
        self.TIME_REVEAL = 10
        self.TIME_NEXT_QUESTION = 5
        self.TIME_NEXT_IMAGE = 10

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.init_game()
        # if self.game_mode != 'chill':
            # self.task_sleep_reveal = asyncio.ensure_future(self.next_reveal())
            # TODO
        self.task_sleep_image = asyncio.ensure_future(self.next_image())


    async def init_game(self):
        self.game, self.questions, self.nb_questions, self.current_q = await self.data_init()

    @database_sync_to_async
    def data_init(self):
        game = Game.objects.get(name=self.game_name)
        questions = QuestionImage.objects.filter(game_id=game.id).order_by('id')
        nb_questions = game.nb_q
        current_q = game.current_q
        return game, questions, nb_questions, current_q

    @database_sync_to_async
    def get_data(self, current_q):
        # Pas sûr que ça doit un vrai accès en base ? sync vraiment nécessaire ?
        q = self.questions[current_q]

        context = {
            'q_id':q.id,
            'movie1_id':q.movie1.id,
            'movie2_id': q.movie2.id,
            'movie3_id': q.movie3.id,
            'movie1_name': q.movie1.name,
            'movie2_name': q.movie2.name,
            'movie3_name': q.movie3.name,
            'movie1_url': str(q.movie1.image),
            'movie2_url': str(q.movie2.image),
            'movie3_url': str(q.movie3.image),
            # 'quote_text': q.quote.quote_text,
            'list_user_id': self.list_id,
            'current_answer': json.dumps(self.dict_current_answer),
            'dict_user': json.dumps(self.dict_user)

        }
        return context

    @database_sync_to_async
    def get_data_image(self, current_q, current_q_image):
        q = self.questions[current_q]
        i = list(Screenshot.objects.filter(pk__in=q.list_image_id.split(',')))[current_q_image]
        context = {
            'q_id':q.id,
            'image_url': str(i.image),
            'list_user_id': self.list_id,
            'current_answer': json.dumps(self.dict_current_answer),
            'dict_user': json.dumps(self.dict_user)

        }
        return context

    @database_sync_to_async
    def incr_current_q(self):
        Game.objects.filter(id=self.game.id).update(current_q=F("current_q") + 1)

    @database_sync_to_async
    def end_current_q(self):
        Game.objects.filter(id=self.game.id).update(current_q=-1)

    @database_sync_to_async
    def compute_score(self, i):
        q = self.questions[i]
        for user_id in self.list_id:
            count = list(AnswerImage.objects.filter(questionimage=q, movie_prop=q.movie_guessed, user_id=user_id).values_list('score', flat=True))
            count = [i if i else 0 for i in count] # Remove None
            if len(count) != 0:
                count = np.sum(count)
            else:
                count = 0
            self.dict_score[user_id] += int(count)
        self.dict_score = dict(sorted(self.dict_score.items(), key=lambda item: item[1], reverse=True))

    async def next_reveal(self):
        # Attend Xs et ordonne de reveal answer
        # 0.5 to take into account delay

        # time_step = int(self.game_mode) + 0.5

        await self.send_reveal()

        # Si mode debrief timer, on attend et envoie la prochaine question
        # if self.game_mode_debrief != 'chill':
            # time_step_debrief = int(self.game_mode_debrief) + 0.5
        time_step_debrief = int(self.TIME_NEXT_QUESTION) + 0.5
        await asyncio.sleep(time_step_debrief)
        await self.next_question_chill()

        # for i in range(1, self.nb_questions):
        #     time_step = int(self.game_mode)
        #     await asyncio.sleep(time_step)
        #
        #     self.dict_current_answer = {user_id: 0 for user_id in self.list_id}
        #     context = await self.get_data(i)
        #     await self.compute_score(i - 1)
        #     context['type'] = 'user_message'
        #     context['code'] = 'idle'
        #     context['dict_score'] = json.dumps(self.dict_score)
        #
        #     await self.incr_current_q()
        #
        #     await self.channel_layer.group_send(self.room_group_name, context)
        #
        # await asyncio.sleep(time_step)
        # await self.end_current_q()
        # await self.disconnect('normal')

    async def next_image(self):
        while self.current_q_image < 2:
            # time_step = int(self.game_mode) + 0.5
            
            time_step = int(self.TIME_NEXT_IMAGE) + 0.5
            await asyncio.sleep(time_step)

            # self.dict_current_answer = {user_id: 0 for user_id in self.list_id}
            # self.dict_score_current = {u_id:0 for u_id in self.dict_score.keys()}
            context = await self.get_data_image(self.current_q, self.current_q_image+1)
            # await self.compute_score(self.current_q)
            context['type'] = 'newimage'
            context['code'] = 'newimage'
            context['n_image'] = self.current_q_image+2
            # context['dict_score'] = json.dumps(self.dict_score)


            # await self.incr_current_q()
            self.current_q_image += 1
            await self.channel_layer.group_send(self.room_group_name, context)


        # else:
        #     pass
            # await self.end_current_q()
            # await self.disconnect('normal')
            # TODO Afficher les 3 choix
        time_step = int(self.TIME_REVEAL) + 0.5
        await asyncio.sleep(time_step)

        self.task_sleep_reveal = asyncio.ensure_future(self.next_reveal())
        

    @database_sync_to_async
    def get_question_id(self):
        return self.questions[self.current_q].id

    async def next_question_chill(self):

        if self.current_q < self.nb_questions - 1:
            self.dict_current_answer = {user_id: 0 for user_id in self.list_id}
            self.dict_score_current = {u_id:0 for u_id in self.dict_score.keys()}
            # context = await self.get_data(self.current_q+1)
            # context = {}
            self.current_q_image = 0

            context = await self.get_data_image(self.current_q+1, self.current_q_image)
            await self.compute_score(self.current_q)
            self.current_q += 1
            context['type'] = 'user_message'
            context['code'] = 'nextquestion'
            context['question_id'] = await self.get_question_id()
            context['dict_score'] = json.dumps(self.dict_score)
            context['list_user_id'] = self.list_id

            
            await self.incr_current_q()
            
            
            await self.channel_layer.group_send(self.room_group_name, context)


            self.task_sleep_image = asyncio.ensure_future(self.next_image())
            
        else:
            await self.end_current_q()
            await self.disconnect('normal')

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message == 'next':
            # Send message to room group
            if self.task_sleep_image != False:
                self.task_sleep_image.cancel()
            if self.task_sleep_reveal != False:
                self.task_sleep_reveal.cancel()
            self.task_sleep_reveal = asyncio.ensure_future(self.next_reveal())
        elif message == 'sleep_reveal':
            # await self.next_reveal()
            self.task_sleep_reveal = asyncio.ensure_future(self.next_reveal())


    @database_sync_to_async
    def change_host(self, new_host):
        Game.objects.filter(id=self.game.id).update(host=new_host)

    async def disconnect(self, close_code):
        # self.close()
        # Normal end
        if close_code == 'normal':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_message',
                    'code': 'end'
                }
            )
        else:
            # Si le game master quitte la page, la partie est arrêtée et on change d'host
            # list_new_host = [u_id for u_id in self.list_id if u_id != self.user_id]
            # if len(list_new_host) != 0:
            #     new_host = list_new_host[0]
            #     new_dict_user = {key: self.dict_user[key] for key in list_new_host}
        
            #     await self.change_host(new_host)

            # Envoie un message pour dire d'arrêter la partie
            context = {
                'type': 'interruption',
                'code': 'interruption',
            }
            
            await self.channel_layer.group_send(self.room_group_name, context)

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    @database_sync_to_async
    def is_correct(self, i, movie_id):
        q = self.questions[i]
        if q.movie_guessed.id == int(movie_id):
            return 1
        else:
            return 0

    @database_sync_to_async
    def update_score_base(self, user_id, current_q, new_score):
        q = self.questions[current_q]
        a = AnswerImage.objects.get(user_id=user_id, questionimage=q)
        a.score = new_score
        a.save()

    async def newanswer(self, event):
        if event['code'] == 'new_answer':
            
            ans = await self.is_correct(self.current_q, event['movie_id'])
            if ans == 1:
                if self.current_q_image == 0:
                    score = 5
                elif self.current_q_image == 1:
                    score = 3
                else:
                    score = 1
                await self.update_score_base(event['user_id'], self.current_q, score)

                self.dict_score_current[event['user_id']] = score
                self.dict_current_answer[event['user_id']] = 1
                context = {
                    'type': 'newansweruser',
                    'code': 'newanswer',
                    'current_answer': json.dumps(self.dict_current_answer),
                    'list_user_id': self.list_id,
                    'dict_user': json.dumps(self.dict_user),
                    'dict_score': json.dumps(self.dict_score)
                }
                await self.channel_layer.group_send(self.room_group_name, context)

                # TODO : Pour eviter les problèmes de concurrence entre next_reveal et ici
                # if self.game_mode == 'chill' or self.game_mode_debrief == 'chill':
                
                # If everybody answered
                if sum(self.dict_current_answer.values()) == len(self.list_id):
                    if self.task_sleep_image != False:
                        self.task_sleep_image.cancel()
                    if self.task_sleep_reveal != False:
                        self.task_sleep_reveal.cancel()

                    self.task_sleep_reveal = asyncio.ensure_future(self.next_reveal())


    async def send_reveal(self):
        context = {
            'type': 'revealanswer',
            'code': 'revealanswer',
            'dict_score_current': json.dumps(self.dict_score_current),
            'list_user_id': self.list_id,
            'dict_user': json.dumps(self.dict_user),
            'dict_score': json.dumps(self.dict_score)
        }
        await self.channel_layer.group_send(self.room_group_name, context)

    async def revealanswer(self, event):
        pass

    async def newansweruser(self, event):
        pass

    async def user_message(self, event):
        pass

    async def newimage(self, event):
        pass

    async def user_updateuser(self, event):
        pass

    async def interruption(self, event):
        pass


class UserConsumerImage(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["session"]["user_id"]
        self.user_name = self.scope["session"]["user_name"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.game_name = self.scope['url_route']['kwargs']['game_name']
        self.room_group_name = 'chat_%s' % self.game_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def interruption(self, data):

        message = {'code': 'interruption'}
        # if data['new_host_id'] == self.user_id:
        #     message['is_new_host'] = '1'
        #     message['new_host_id'] = data['new_host_id']
        #     message['new_dict_user'] = data['new_dict_user']
        # else:
        #     message['is_new_host'] = '0'

        await self.send(text_data=json.dumps(message))

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if message == 'new_answer':
            # Send message to room group
            context = {
                'type': 'newanswer',
                'code': 'new_answer',
                'user_id': self.user_id,
                'movie_id': text_data_json['movie_id'],
                'ok': text_data_json['ok']
            }
            await self.channel_layer.group_send(self.room_group_name, context)


    async def user_message(self, data):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(data))

    async def newimage(self, data):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(data))

    async def newansweruser(self, data):
        # Send message to WebSocket
        context = {'code': 'newanswer',
                   'current_answer': data['current_answer'],
                   'list_user_id': data['list_user_id'],
                   'dict_user': data['dict_user'],
                   'dict_score': data['dict_score'],
                   }
        await self.send(text_data=json.dumps(context))

    async def revealanswer(self, data):
        context = {'code': 'reveal',
                   'dict_score_current': data['dict_score_current'],
                   'list_user_id': data['list_user_id'],
                   'dict_user': data['dict_user'],
                   'dict_score': data['dict_score'],
                   }
         
        await self.send(text_data=json.dumps(context))

    async def user_connection(self, event):
        pass

    async def newanswer(self, event):
        pass


#######################
# Room home
#######################

class GameMasterConsumerHome(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'home_%s' % self.room_name
        self.list_id = [self.user_id]
        self.mode = self.scope["session"]["mode"]

        # Pour chaque id correspond le nom d'user
        self.dict_user = {}

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_refresh',
                    'code': 'event_refresh',
                    'host_id': self.user_id,
                }
            )

        
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        game_name = text_data_json['game_name']
        mode = text_data_json['mode']

        if message == 'go':
            # Send message to room group
            self.mode = mode
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_start',
                    'code': 'event_start',
                    'game_name': game_name,
                    'dict_user': self.dict_user,
                    'mode': mode
                }
            )


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def user_start(self, event):
        pass

    async def user_updateuser(self, event):
        pass

    async def user_refresh(self, event):
        pass

    async def user_connection(self, event):
        new_user_id = event['user_id']
        new_user_name = event['user_name']
        self.dict_user[new_user_id] = new_user_name
        self.list_id.append(new_user_id)
        self.list_id = list(set(self.list_id))

        # Send message to WebSocket
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user.updateuser',
                'list_user_id': self.list_id,
                'dict_user':  self.dict_user,
                'code':'idle'
            }
        )

    async def user_deconnection(self, event):
        old_user_id = event['user_id']
        if old_user_id != self.user_id:
            if old_user_id in self.list_id:
                self.list_id.remove(old_user_id)
            if old_user_id in self.dict_user.keys():
                del self.dict_user[old_user_id]

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user.updateuser',
                    'list_user_id': self.list_id,
                    'dict_user':  self.dict_user,
                    'code':'idle'
                }
            )


class UserConsumerHome(AsyncWebsocketConsumer):
    async def connect(self):
        # self.user_id = self.scope['url_route']['kwargs']['user_id']
        # self.user_name = self.scope['url_route']['kwargs']['user_name']
        self.user_id = self.scope["session"]["user_id"]
        self.user_name = self.scope["session"]["user_name"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'home_%s' % self.room_name
        self.end = False

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.hello()


    async def hello(self):
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user.connection',
                'user_id': self.user_id,
                'user_name': self.user_name
            }
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user_name = text_data_json['user_name']
        self.user_name = user_name

        await self.hello()



    async def user_start(self, event):
        code = event['code']
        game_name = event['game_name']
        dict_user = event['dict_user']
        mode = event['mode']
        self.end = True

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'code': 'event_start',
            'mode': mode,
            'game_name': game_name,
            'list_user': list(dict_user.values())
        }))

    async def disconnect(self, close_code):
        # Leave room group
        if not self.end:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user.deconnection',
                    'user_id': self.user_id,
                }
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def user_updateuser(self, event):
        code = 'idle'
        list_user_id = event['list_user_id']
        dict_user = event['dict_user']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            {
                'code': code,
                'list_user_id':list_user_id,
                'dict_user': dict_user
            }
        ))

    async def user_refresh(self, event):

        if event['host_id'] != self.user_id:
            await self.send(text_data=json.dumps(
                {
                    'code': 'refresh',
                    'dict_user': {}
                }
            ))

    async def user_connection(self, event):
        pass

    async def user_deconnection(self, event):
        pass


#######################
# Room results
#######################



class GameMasterConsumerResults(AsyncWebsocketConsumer):
    async def connect(self):
        # self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'results_%s' % self.room_name
        # self.list_id = [self.user_id]

        # Pour chaque id correspond le nom d'user
        # self.dict_user = {}

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        # game_name = text_data_json['game_name']

        if message == 'new_game':
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_message',
                    'code': 'event_new',
                }
            )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def user_message(self, event):
        pass



class UserConsumerResults(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'results_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def user_message(self, data):
        await self.send(text_data=json.dumps(data))


    async def disconnect(self, close_code):
        # Leave room group

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )