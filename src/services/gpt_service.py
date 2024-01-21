import logging


# Function to generate user-friendly explanations using GPT-3
def generate_gpt_explanation(openai_client, text, model="gpt-3.5-turbo"):
    prompt = (
        "Hi there, I am a patient and just had a doctor's visit. My doctor just gave me a note with this information, but I don't understand it. Below is the text that is on the note, can you try your best to explain to me what it says in a way that I can easily understand and also provide me with online resources regarding what it talks about? Ignore anything that does not make sense.\n\n"
        "Note:\n" + text
    )
    try:
        logging.info("Sending prompt to GPT-3")
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = response.choices[0].message.content
        return explanation
    except Exception as e:
        logging.error(f"Error generating explanation: {e}")
        raise
