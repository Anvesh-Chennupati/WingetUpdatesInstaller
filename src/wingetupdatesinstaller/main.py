import gradio as gr
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def greet():
    logger.info("Button clicked - generating greeting")
    return "Hello, World!"

def create_app():
    logger.info("Creating Gradio application")
    with gr.Blocks(title="WingetUpdatesInstaller") as app:
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Welcome to WingetUpdatesInstaller")
                button = gr.Button("Click Me!", variant="primary")
                output = gr.Textbox(label="Output")
                button.click(
                    fn=greet,
                    outputs=output,
                    api_name="greet"
                )
    return app

def main():
    logger.info("Starting WingetUpdatesInstaller GUI...")
    app = create_app()
    logger.info("Launching server on http://localhost:10001")
    app.launch(
        server_port=10001,
        server_name="0.0.0.0",
        quiet=False,  # Enable Gradio server logs
    )

if __name__ == "__main__":
    main()
