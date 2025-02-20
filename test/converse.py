# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module contains the frontend gui for having a conversation."""
import functools
import logging
from typing import Any, Dict, List, Tuple, Union

import gradio as gr

from frontend import assets, chat_client, asr_utils, tts_utils

_LOGGER = logging.getLogger(__name__)
PATH = "/converse"
TITLE = "Converse"
OUTPUT_TOKENS = 4096
MAX_DOCS = 5

# Edit data below for specific demos ----
EXAMPLE_TITLES = [
                     "### Technical Support",
                     "### Marketing",
                     "### Financial Analysis",
                     "### Sales",
                     "### Coding Assistant",
                 ]
EXAMPLES = [

###TECH SUPPPORT

               [
                   "Please document the process  of a cluster aware update for Dell VXrail.",
                   "Can you tell me more about Dell PowerEdge Carbonblack security features?",
                   "How do I configure disaster recovery using Dell Powerflex for my on-premises data center?",

               ],

### MARKETING

				[ 

					"Create an ad for Dell Technologies PowerEdge servers with an interesting headline and product description. Provide your answer first in English, and then in French language.",
                   "Create 3 engaging tweets highlighting the key advantages of using Dell Technologies solutions for Generative AI.",
				   "Outline a fun social media campaign that takes followers on a virtual world tour of Dell's global sustainability efforts using engaging storytelling."
               ],

### FINANCIAL ANALYSIS

               [
                   "Summarize the key financial takeaways from Dell’s latest SEC filings, focusing on investment opportunities and risk factors.",
                   "Provide an analysis of the competitive landscape based on Nvidia’s latest SEC filings, identify trends and opportunities for strategic positioning.",
				   "Compare Dell's financial performance with its main competitors in the storage market, focusing on revenue and market share."
               ],

### SALES

               [
                   "Sketch an account plan that positions Dell Technologies protection storage as the customer's best choice.",
                   "Create a comparison list of the pro's and con's between Dell Technologies Powerflex storage solutions against HP storage solutions.",
                   "What are the key steps in designing a secure and scalable on-premises solution for GenAI workloads with Dell?",

               ],


### CODING ASSISTANT

               [
                   "Provide a Python code for setting up a Flask server that serves static files from a directory named 'static'.",
                   "Provide an example of a Dockerfile for a Python-based machine learning project that includes installing PyTorch and NumPy.",
                   "How do I use Python's Pandas library to read a CSV file and filter rows based on a column's value?",

               ]


           ]
# ----------------------------------------

_LOCAL_CSS = """

#contextbox {
    overflow-y: scroll !important;
    max-height: 400px;
}
"""


def build_page(client: chat_client.ChatClient) -> gr.Blocks:
    """Build the gradio page to be mounted in the frame."""
    kui_theme, kui_styles = assets.load_theme("kaizen")

    with gr.Blocks(title=TITLE, theme=kui_theme, css=kui_styles + _LOCAL_CSS) as page:

        # session specific state across runs
        state = gr.State(value=asr_utils.ASRSession())

        with gr.Row():
            gr.Image("dell_tech.png", scale=0.2, show_download_button=False, show_label=False, container=False)
#            gr.Markdown("                       ")
#            gr.Image("nvidia.png", scale=0, show_download_button=False, show_label=False, container=False)

        # create the page header
        gr.Markdown(f"# {TITLE}")

        # chat logs
        with gr.Row(equal_height=True):
            #chatbot = gr.Chatbot(scale=2, label=client.model_name)
            chatbot = gr.Chatbot(scale=2, label=client.model_name, bubble_full_width=False)
            latest_response = gr.Textbox(visible=False)
            context = gr.JSON(
                scale=1,
                label="Knowledge Base Context",
                visible=False,
                elem_id="contextbox",
            )

        # TTS output box
        # visible so that users can stop or replay playback
        #with gr.Row():
        #    output_audio = gr.Audio(
        #        label="Synthesized Speech",
        #        autoplay=True,
        #        interactive=False,
        #        streaming=True,
        #        visible=True,
        #        show_download_button=False
        #    )

        # check boxes
        with gr.Row():
            with gr.Column(scale=10, min_width=150):
                kb_checkbox = gr.Checkbox(
                    label="Use knowledge base", info="", value=False
                )
            #with gr.Column(scale=10, min_width=150):
            #    tts_checkbox = gr.Checkbox(
            #        label="Enable TTS output", info="", value=False
            #    )
        
        # dropdowns
        #with gr.Accordion("ASR and TTS Settings"):
        #    with gr.Row():
        #        asr_language_list = list(asr_utils.ASR_LANGS)
        #        asr_language_dropdown = gr.components.Dropdown(
        #            label="ASR Language",
        #            choices=asr_language_list,
        #            value=asr_language_list[0],
        #        )
        #        tts_language_list = list(tts_utils.TTS_MODELS)
        #        tts_language_dropdown = gr.components.Dropdown(
        #            label="TTS Language",
        #            choices=tts_language_list,
        #            value=tts_language_list[0],
        #        )
        #        all_voices = []
        #        try:
        #            for model in tts_utils.TTS_MODELS:
        #                all_voices.extend(tts_utils.TTS_MODELS[model]['voices'])
        #            default_voice = tts_utils.TTS_MODELS[tts_language_list[0]]['voices'][0]                    
        #        except:
        #            all_voices.append("No TTS voices available")
        #            default_voice = "No TTS voices available"
        #        tts_voice_dropdown = gr.components.Dropdown(
        #            label="TTS Voice",
        #            choices=all_voices,
        #            value=default_voice,
        #        )

        # audio and text input boxes
        with gr.Row():
            with gr.Column(scale=10, min_width=500):
                msg = gr.Textbox(
                    show_label=False,
                    placeholder="Enter text and press ENTER",
                    container=False,
                )
            # For (at least) Gradio 3.39.0 and lower, the first argument
            # in the list below is named `source`. If not None, it must
            # be a single string, namely either "upload" or "microphone".
            # For more recent Gradio versions (such as 4.4.1), it's named
            # `sources`, plural. If not None, it must be a list, containing
            # either "upload", "microphone", or both.
            #audio_mic = gr.Audio(
            #    sources=["microphone"],
            #    type="numpy",
            #    streaming=True,
            #    visible=True,
            #    label="Transcribe Audio Query",
            #    show_label=False,
            #    container=False,
            #    elem_id="microphone",
            #)

        # user feedback
        with gr.Row():
            # _ = gr.Button(value="👍  Upvote")
            # _ = gr.Button(value="👎  Downvote")
            # _ = gr.Button(value="⚠️  Flag")
            submit_btn = gr.Button(value="Submit")
            _ = gr.ClearButton(msg)
            _ = gr.ClearButton([msg, chatbot], value="Clear History")
            ctx_show = gr.Button(value="Show Context")
            ctx_hide = gr.Button(value="Hide Context", visible=False)



        def example_click(user_input):
            return user_input

        title_counter = 0
        for list_entry in EXAMPLES:
            if len(EXAMPLE_TITLES[title_counter]) > 0:
                gr.Markdown(EXAMPLE_TITLES[title_counter])
            with gr.Row():
                for entry in list_entry:
                    button = gr.Button(entry)
                    button.click(fn=example_click, inputs=button, outputs=msg)
                title_counter += 1



        # hide/show context
        def _toggle_context(btn: str) -> Dict[gr.component, Dict[Any, Any]]:
            if btn == "Show Context":
                out = [True, False, True]
            if btn == "Hide Context":
                out = [False, True, False]
            return {
                context: gr.update(visible=out[0]),
                ctx_show: gr.update(visible=out[1]),
                ctx_hide: gr.update(visible=out[2]),
            }

        ctx_show.click(_toggle_context, [ctx_show], [context, ctx_show, ctx_hide])
        ctx_hide.click(_toggle_context, [ctx_hide], [context, ctx_show, ctx_hide])

        # form actions
        _my_build_stream = functools.partial(_stream_predict, client)
        msg.submit(
            _my_build_stream, [kb_checkbox, msg, chatbot], [msg, chatbot, context, latest_response]
        )
        submit_btn.click(
            _my_build_stream, [kb_checkbox, msg, chatbot], [msg, chatbot, context, latest_response]
        )

        #tts_language_dropdown.change(
        #    tts_utils.update_voice_dropdown, 
        #    [tts_language_dropdown], 
        #    [tts_voice_dropdown], 
        #    api_name=False
        #)

        #audio_mic.start_recording(
        #    asr_utils.start_recording,
        #    [audio_mic, asr_language_dropdown, state],
        #    [msg, state],
        #    api_name=False,
        #)
        #audio_mic.stop_recording(
        #    asr_utils.stop_recording,
        #    [state],
        #    [state],
        #    api_name=False
        #)
        #audio_mic.stream(
        #    asr_utils.transcribe_streaming,
        #    [audio_mic, asr_language_dropdown, state],
        #    [msg, state],
        #    api_name=False
        #)
        #audio_mic.clear(
        #    lambda: "",
        #    [],
        #    [msg],
        #    api_name=False
        #)

        #latest_response.change(
        #    tts_utils.text_to_speech,
        #    [latest_response, tts_language_dropdown, tts_voice_dropdown, tts_checkbox],
        #    [output_audio],
        #    api_name=False
        #)

    page.queue()
    return page


def _stream_predict(
    client: chat_client.ChatClient,
    use_knowledge_base: bool,
    question: str,
    chat_history: List[Tuple[str, str]],
) -> Any:
    """Make a prediction of the response to the prompt."""
    chunks = ""
    chat_history = chat_history or []
    _LOGGER.info(
        "processing inference request - %s",
        str({"prompt": question, "use_knowledge_base": use_knowledge_base}),
    )

    documents: Union[None, List[Dict[str, Union[str, float]]]] = None
    if use_knowledge_base:
        documents = client.search(prompt = question)

    for chunk in client.predict(query=question, use_knowledge_base=use_knowledge_base, num_tokens=OUTPUT_TOKENS):
        if chunk:
            chunks += chunk
            yield "", chat_history + [[question, chunks]], documents, ""
        else:
            yield "", chat_history + [[question, chunks]], documents, chunks
