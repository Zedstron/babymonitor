let pendingCandidates = [];
let vidMuted = true;

async function initWebRTC() 
{
    document.getElementById("vid-mute-btn").addEventListener("touchstart", toggleVidMute);
    await clearExistingWebRTCConnection();

    const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
    });

    pc.ontrack = (event) => {
        const video = document.getElementById("remoteVideo");

        if (!video.srcObject)
            video.srcObject = new MediaStream();

        video.srcObject.addTrack(event.track);

        video.play().catch(err => {
            console.error("Video play failed:", err);
        });
    };

    pc.addTransceiver("video", { direction: "recvonly" });
    pc.addTransceiver("audio", { direction: "recvonly" });

    const offer = await pc.createOffer();

    await pc.setLocalDescription(offer);

    const res = await fetch("/streaming/offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pc.localDescription)
    });

    const data = await res.json();

    window.pc_id = data.id;
    localStorage.setItem("pc_id", data.id);

    await pc.setRemoteDescription({
        sdp: data.sdp,
        type: data.type
    });
}

async function clearExistingWebRTCConnection()
{
    const pc_id = localStorage.getItem("pc_id");
    if (window.pc_id && pc_id)
    {
        await fetch("/streaming/close", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pc_id })
        });
    }
}

function toggleVidMute()
{
    vidMuted = !vidMuted;
    if (vidMuted)
        document.getElementById("vid-mute-icon").className = "fa-solid fa-volume-mute";
    else
        document.getElementById("vid-mute-icon").className = "fa-solid fa-volume-high";

    document.getElementById("remoteVideo").muted = vidMuted;
}