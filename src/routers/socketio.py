from datetime import datetime
from helpers.logger import logger

def create_router(state, sio):
    @sio.event
    async def connect(sid, environ):
        logger.info(f"🟢 Client connected: {sid}")
        
        state.connected_clients[sid] = {
            "connected_at": datetime.now().isoformat(),
            "ip": environ.get('REMOTE_ADDR', 'unknown')
        }

        await sio.emit('initial_state', {
            "sensor_data": state.sensor_data,
            "settings": state.settings,
            "is_connected": True,
            "notifications": state.notifications[-10:],
            "is_recording": state.is_recording,
        }, room=sid)

        await sio.emit('client_count', { "count": len(state.connected_clients) })

    @sio.event
    async def disconnect(sid):
        logger.info(f"🔴 Client disconnected: {sid}")
        
        if sid in state.connected_clients:
            del state.connected_clients[sid]

        await sio.emit('client_count', { "count": len(state.connected_clients) })

    @sio.event
    async def ping(sid, data):
        await sio.emit("pong", data, to=sid)