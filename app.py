import os
import tempfile

import streamlit as st
import streamlit.components.v1 as components

from resume_processing import (
    process_uploaded_resume,
    create_interview_questions,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Mock Interview Assistant",
    page_icon="🎤",
    layout="wide",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #777;
        font-size: 18px;
        margin-bottom: 35px;
    }

    .question-box {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 12px;
        background-color: #fafafa;
        font-size: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🎤 AI Mock Interview Assistant</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Practice interviews using your resume"
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "questions" not in st.session_state:
    st.session_state.questions = None

if "resume_profile" not in st.session_state:
    st.session_state.resume_profile = None


# =========================================================
# RESUME UPLOAD
# =========================================================

st.subheader("📄 Upload Your Resume")

uploaded_file = st.file_uploader(
    "Upload your resume in PDF format",
    type=["pdf"],
)


# =========================================================
# PROCESS RESUME
# =========================================================

if uploaded_file is not None:

    st.success(
        f"Resume uploaded: {uploaded_file.name}"
    )

    if st.button(
        "✨ Generate Interview Questions",
        type="primary",
        use_container_width=True,
    ):

        temp_file_path = None

        try:

            # Save uploaded PDF temporarily
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf",
            ) as temp_file:

                temp_file.write(
                    uploaded_file.getbuffer()
                )

                temp_file_path = temp_file.name

            # ---------------------------------------------
            # STEP 1: PROCESS RESUME
            # ---------------------------------------------

            with st.spinner(
                "📖 Reading and analyzing your resume..."
            ):

                resume_profile = process_uploaded_resume(
                    temp_file_path
                )

            st.session_state.resume_profile = resume_profile

            # ---------------------------------------------
            # STEP 2: GENERATE QUESTIONS
            # ---------------------------------------------

            with st.spinner(
                "🤖 Generating personalized interview questions..."
            ):

                questions = create_interview_questions(
                    resume_profile
                )

            questions = questions[:8]

            if questions:

                st.session_state.questions = questions

                st.success(
                    f"✅ {len(questions)} interview questions generated!"
                )

            else:

                st.error(
                    "No interview questions were generated."
                )

        except Exception as e:

            st.error(
                f"An error occurred:\n\n{e}"
            )

        finally:

            if (
                temp_file_path
                and os.path.exists(temp_file_path)
            ):

                os.remove(temp_file_path)


# =========================================================
# DISPLAY GENERATED QUESTIONS
# =========================================================

if st.session_state.questions:

    st.divider()

    st.subheader("📝 Generated Interview Questions")

    for i, question in enumerate(
        st.session_state.questions,
        start=1,
    ):

        st.markdown(
            f"""
            <div class="question-box">
                <strong>Question {i}</strong>
                <br><br>
                {question}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        "🎯 These questions were generated from your resume."
    )


    # =====================================================
    # START INTERVIEW
    # =====================================================

    st.divider()

    st.subheader("🎥 Start Mock Interview")

    # Convert questions into JavaScript-safe JSON
    import json

    questions_json = json.dumps(
        st.session_state.questions
    )

    interview_html = f"""
    <!DOCTYPE html>

    <html>

    <head>

    <meta charset="UTF-8">

    <style>

        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 10px;
            background: white;
        }}

        .container {{
            max-width: 900px;
            margin: auto;
            text-align: center;
        }}

        video {{
            width: 100%;
            max-width: 720px;
            border-radius: 12px;
            background: black;
            margin-top: 15px;
        }}

        .question {{
            font-size: 22px;
            font-weight: bold;
            padding: 20px;
            margin-top: 15px;
            border-radius: 12px;
            background: #f5f5f5;
        }}

        .timer {{
            font-size: 32px;
            font-weight: bold;
            margin: 15px;
        }}

        .counter {{
            font-size: 18px;
            margin: 10px;
        }}

        button {{
            padding: 12px 22px;
            margin: 8px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }}

        #startBtn {{
            background: #111;
            color: white;
        }}

        #pauseBtn {{
            background: #777;
            color: white;
            display: none;
        }}

        #downloadBtn {{
            background: #16803c;
            color: white;
            display: none;
        }}

        .status {{
            margin-top: 15px;
            font-weight: bold;
        }}

    </style>

    </head>


    <body>

    <div class="container">

        <div class="counter" id="counter">
            Ready to start
        </div>

        <div class="question" id="question">
            Click START INTERVIEW to begin.
        </div>

        <div class="timer" id="timer">
            ⏱️ 30 seconds
        </div>

        <video
            id="video"
            autoplay
            muted
            playsinline>
        </video>

        <br>

        <button id="startBtn">
            ▶ START INTERVIEW
        </button>

        <button id="pauseBtn">
            ⏸ PAUSE
        </button>

        <button id="downloadBtn">
            💾 DOWNLOAD RECORDING
        </button>

        <div class="status" id="status">
            Camera and microphone will start when you click START.
        </div>

    </div>


    <script>

        const questions = {questions_json};

        let currentQuestion = 0;

        let timeLeft = 30;

        let timerInterval = null;

        let stream = null;

        let mediaRecorder = null;

        let recordedChunks = [];

        let isPaused = false;

        let interviewFinished = false;


        const video =
            document.getElementById("video");

        const question =
            document.getElementById("question");

        const counter =
            document.getElementById("counter");

        const timer =
            document.getElementById("timer");

        const status =
            document.getElementById("status");

        const startBtn =
            document.getElementById("startBtn");

        const pauseBtn =
            document.getElementById("pauseBtn");

        const downloadBtn =
            document.getElementById("downloadBtn");


        // =================================================
        // DISPLAY QUESTION
        // =================================================

        function displayQuestion() {{

            question.innerText =
                questions[currentQuestion];

            counter.innerText =
                "Question " +
                (currentQuestion + 1) +
                " of " +
                questions.length;

            timeLeft = 30;

            timer.innerText =
                "⏱️ " +
                timeLeft +
                " seconds";
        }}


        // =================================================
        // TIMER
        // =================================================

        function startTimer() {{

            clearInterval(timerInterval);

            timerInterval = setInterval(() => {{

                if (isPaused)
                    return;

                timeLeft--;

                timer.innerText =
                    "⏱️ " +
                    timeLeft +
                    " seconds";


                if (timeLeft <= 0) {{

                    clearInterval(timerInterval);

                    nextQuestion();

                }}

            }}, 1000);

        }}


        // =================================================
        // NEXT QUESTION
        // =================================================

        function nextQuestion() {{

            if (currentQuestion <
                questions.length - 1) {{

                currentQuestion++;

                displayQuestion();

                startTimer();

            }}

            else {{

                finishInterview();

            }}

        }}


        // =================================================
        // START INTERVIEW
        // =================================================

        startBtn.onclick = async function() {{

            try {{

                stream =
                    await navigator.mediaDevices
                    .getUserMedia({{
                        video: true,
                        audio: true
                    }});


                video.srcObject = stream;


                recordedChunks = [];


                mediaRecorder =
                    new MediaRecorder(stream);


                mediaRecorder.ondataavailable =
                    function(event) {{

                        if (event.data.size > 0) {{

                            recordedChunks.push(
                                event.data
                            );

                        }}

                    }};


                mediaRecorder.start();


                currentQuestion = 0;

                interviewFinished = false;

                isPaused = false;


                displayQuestion();

                startTimer();


                startBtn.style.display =
                    "none";

                pauseBtn.style.display =
                    "inline-block";


                status.innerText =
                    "🔴 Interview in progress...";


            }}

            catch(error) {{

                status.innerText =
                    "❌ Camera/microphone permission was denied.";

                console.error(error);

            }}

        }};


        // =================================================
        // PAUSE / RESUME
        // =================================================

        pauseBtn.onclick = function() {{

            if (!isPaused) {{

                isPaused = true;

                pauseBtn.innerText =
                    "▶ RESUME";

                status.innerText =
                    "⏸ Interview paused.";

            }}

            else {{

                isPaused = false;

                pauseBtn.innerText =
                    "⏸ PAUSE";

                status.innerText =
                    "🔴 Interview resumed.";

            }}

        }};


        // =================================================
        // FINISH INTERVIEW
        // =================================================

        function finishInterview() {{

            if (interviewFinished)
                return;

            interviewFinished = true;

            clearInterval(timerInterval);


            if (mediaRecorder &&
                mediaRecorder.state !== "inactive") {{

                mediaRecorder.stop();

            }}


            if (stream) {{

                stream
                    .getTracks()
                    .forEach(track => track.stop());

            }}


            question.innerText =
                "🎉 Interview Completed!";

            counter.innerText =
                "8 of 8 questions completed";

            timer.innerText =
                "✅ Finished";


            pauseBtn.style.display =
                "none";


            status.innerText =
                "Interview recording is ready.";


            // Give MediaRecorder time to finish
            setTimeout(() => {{

                downloadRecording();

            }}, 1000);

        }}


        // =================================================
        // DOWNLOAD RECORDING
        // =================================================

        function downloadRecording() {{

            if (recordedChunks.length === 0) {{

                status.innerText =
                    "⚠️ No recording data was created.";

                return;

            }}


            const blob =
                new Blob(
                    recordedChunks,
                    {{ type: "video/webm" }}
                );


            const url =
                URL.createObjectURL(blob);


            const a =
                document.createElement("a");


            a.href = url;

            a.download =
                "AI_Mock_Interview.webm";


            document.body.appendChild(a);

            a.click();

            a.remove();


            URL.revokeObjectURL(url);


            downloadBtn.style.display =
                "inline-block";


            status.innerText =
                "✅ Interview completed and recording downloaded.";

        }}


        // =================================================
        // MANUAL DOWNLOAD BUTTON
        // =================================================

        downloadBtn.onclick =
            function() {{

                downloadRecording();

            }};

    </script>

    </body>

    </html>
    """

    components.html(
        interview_html,
        height=850,
        scrolling=True,
    )