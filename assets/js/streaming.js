let pendingCandidates = [];

async function initWebRTC() {
    const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
    });

    pc.addTransceiver("video", { direction: "recvonly" });
    pc.addTransceiver("audio", { direction: "recvonly" });

    pc.onicecandidate = async (event) => {
        if (!event.candidate) return;

        if (!window.pc_id) {
            pendingCandidates.push(event.candidate);
            return;
        }

        sendCandidate(event.candidate);
    };

    pc.ontrack = (event) => {
        const stream = event.streams[0];

        const video = document.getElementById("remoteVideo");
        video.srcObject = stream;

    };

    const offer = await pc.createOffer();

    await pc.setLocalDescription(offer);

    const res = await fetch("/streaming/offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pc.localDescription)
    });

    const data = await res.json();

    window.pc_id = data.id;

    await pc.setRemoteDescription({
        sdp: data.sdp,
        type: data.type
    });

    for (const c of pendingCandidates) {
        await sendCandidate(c);
    }
    pendingCandidates = [];
}

async function sendCandidate(candidate) {
    await fetch("/streaming/candidate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            pc_id: window.pc_id,
            candidate: candidate.candidate,
            sdpMid: candidate.sdpMid,
            sdpMLineIndex: candidate.sdpMLineIndex
        })
    });
}