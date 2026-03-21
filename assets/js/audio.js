let pttActive = false;
let pttTimer = null;
let babyAudioState = {
    listenEnabled: true,
    volume: 70
};

async function initPTT() 
{
    const btn = document.getElementById("ptt-button")
    const bars = document.querySelectorAll("#mic-bars div")
    const status = document.getElementById("ptt-status")

    let stream
    let mediaRecorder
    let chunks = []

    let audioContext
    let analyser
    let dataArray

    function updateBars() {

        analyser.getByteFrequencyData(dataArray)

        for (let i = 0; i < bars.length; i++) {

            let v = dataArray[i] / 255
            let h = Math.max(2, v * 40)

            bars[i].style.height = h + "px"
        }

        if (mediaRecorder && mediaRecorder.state === "recording") {
            requestAnimationFrame(updateBars)
        }
    }

    async function startRecording() 
    {
        if (!stream) {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }

        audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);

        analyser = audioContext.createAnalyser();
        analyser.fftSize = 64;

        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        source.connect(analyser);

        mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/wav" });

        chunks = [];

        mediaRecorder.ondataavailable = e => chunks.push(e.data);

        mediaRecorder.start();

        status.innerText = "Recording ...";

        updateBars();
    }

    function stopRecording() {
        if (!mediaRecorder) return

        status.innerText = "Processing ..."

        mediaRecorder.onstop = async () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }

            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }

            status.innerText = "Playing ...";
            bars.forEach(b => b.style.height = "2px")

            const blob = new Blob(chunks, { type: "audio/webm" })

            const buffer = await blob.arrayBuffer()

            await fetch("/api/audio/play", {
                method: "POST",
                headers: {
                    "Content-Type": "application/octet-stream"
                },
                body: buffer
            });

            status.innerText = "Idle";
            mediaRecorder = null;
        }

        mediaRecorder.stop()
    }

    btn.addEventListener("mousedown", startRecording)
    btn.addEventListener("touchstart", e => {
        e.preventDefault()
        startRecording()
    }, { passive:false });

    btn.addEventListener("mouseup", stopRecording)
    btn.addEventListener("mouseleave", stopRecording)
    btn.addEventListener("touchend", stopRecording)

}

function initBabyAudio() {
    document.getElementById('baby-audio-listen').addEventListener('change', (e) => {
        babyAudioState.listenEnabled = e.target.checked;
        fetch("/api/audio/listen", {
            method: "POST",
            body: JSON.stringify({ status: e.target.checked }),
            headers: {
                "Content-Type": "application/json"
            }
        }, data => {
            if (data.status)
                showToast(data.message, "success");
            else
                showToast(data.message || 'Failed to update listen state', 'error');
        });
    });
}

function updateBabyVolume(value) {
    babyAudioState.volume = parseInt(value);
    document.getElementById('baby-volume-value').textContent = `${value}%`;
    fetch("/api/audio/volume", {
        method: "POST",
        body: JSON.stringify({ volume: value }),
        headers: {
            "Content-Type": "application/json"
        }
    });
}

function getBabyAudioState() {
    return {
        listenEnabled: document.getElementById('baby-audio-listen').checked,
        volume: babyAudioState.volume
    };
}