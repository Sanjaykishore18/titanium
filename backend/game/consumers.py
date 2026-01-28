import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Team, TeamRoundProgress, PageProgress


class GameSyncConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.team_id = self.scope["url_route"]["kwargs"]["team_id"]
        self.round_number = self.scope["url_route"]["kwargs"]["round_number"]

        self.room_group_name = f"game_team_{self.team_id}_round_{self.round_number}"

        # Join WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send current game state to the newly connected user
        state = await self.get_game_state()
        await self.send(
            text_data=json.dumps({
                "type": "game_state",
                "data": state
            })
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "bug_fixed":
            await self.handle_bug_fixed(data)

        elif message_type == "page_completed":
            await self.handle_page_completed(data)

        elif message_type == "sync_request":
            state = await self.get_game_state()
            await self.send(
                text_data=json.dumps({
                    "type": "game_state",
                    "data": state
                })
            )

    async def handle_bug_fixed(self, data):
        page_number = data.get("page_number")
        bug_id = data.get("bug_id")
        username = data.get("user", "Teammate")

        # Broadcast to all team members
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "bug_fixed_broadcast",
                "page_number": page_number,
                "bug_id": bug_id,
                "user": username
            }
        )

    async def handle_page_completed(self, data):
        page_number = data.get("page_number")
        username = data.get("user", "Teammate")

        # Broadcast page completion to ALL team members
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "page_completed_broadcast",
                "page_number": page_number,
                "user": username
            }
        )

        # Also send updated game state to everyone
        state = await self.get_game_state()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_state_broadcast",
                "data": state
            }
        )

    async def bug_fixed_broadcast(self, event):
        await self.send(
            text_data=json.dumps({
                "type": "bug_fixed",
                "page_number": event["page_number"],
                "bug_id": event["bug_id"],
                "user": event["user"]
            })
        )

    async def page_completed_broadcast(self, event):
        await self.send(
            text_data=json.dumps({
                "type": "page_completed",
                "page_number": event["page_number"],
                "user": event["user"]
            })
        )

    async def game_state_broadcast(self, event):
        """Broadcast updated game state to all connected clients"""
        await self.send(
            text_data=json.dumps({
                "type": "game_state",
                "data": event["data"]
            })
        )

    @database_sync_to_async
    def get_game_state(self):
        try:
            team = Team.objects.get(id=self.team_id)

            team_round = TeamRoundProgress.objects.get(
                team=team,
                round__round_number=self.round_number
            )

            pages = PageProgress.objects.filter(
                team_round=team_round
            ).order_by("page_number")

            return {
                "team_name": team.team_name,
                "round_number": self.round_number,
                "current_page": team_round.current_page,
                "score": team_round.score,
                "status": team_round.status,
                "pages": [
                    {
                        "page_number": page.page_number,
                        "completed": page.completed,
                        "bugs_fixed": page.bugs_fixed
                    }
                    for page in pages
                ]
            }

        except Team.DoesNotExist:
            return {"error": "Team not found"}

        except TeamRoundProgress.DoesNotExist:
            return {"error": "Round progress not found"}

        except Exception as e:
            return {"error": str(e)}