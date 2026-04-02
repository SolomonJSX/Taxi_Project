import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Группируем всех водителей в одну "комнату"
        await self.channel_layer.group_add("drivers", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("drivers", self.channel_name)

    # Метод, который будет вызываться, когда придет новый заказ
    async def new_order_notification(self, event):
        # Отправляем данные прямо в браузер водителя
        await self.send(text_data=json.dumps(event["order"]))