from datetime import datetime
from helpers.logger import logger

def create_router(sio):
    @sio.event
    async def connect(sid, environ):
        logger.info(f"🟢 Client connected: {sid}")

        sio.appstate.connected_clients[sid] = {
            "connected_at": datetime.now().isoformat(),
            "ip": environ.get('REMOTE_ADDR', 'unknown')
        }

        await sio.emit('initial_state', {
            "sensor_data": sio.appstate.sensor_data,
            "settings": sio.appstate.settings,
            "is_connected": True,
            "notifications": sio.appstate.notifications[-10:],
            "is_recording": sio.appstate.is_recording,
        }, room=sid)

        await sio.emit('client_count', { "count": len(sio.appstate.connected_clients) })

    @sio.event
    async def disconnect(sid):
        logger.info(f"🔴 Client disconnected: {sid}")
        
        if sid in sio.appstate.connected_clients:
            del sio.appstate.connected_clients[sid]

        await sio.emit('client_count', { "count": len(sio.appstate.connected_clients) })

    @sio.event
    async def ping(sid, data):
        await sio.emit("pong", data, to=sid)