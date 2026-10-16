from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


class LocalLLM:
    """Wrapper para ejecutar Qwen2.5-0.5B-Instruct localmente."""

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        max_new_tokens: int = 80,
    ):
        self.max_new_tokens = max_new_tokens

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        dtype = (
            torch.float16
            if self.device.type == "cuda"
            else torch.float32
        )

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
        )

        self.model.to(self.device)
        self.model.eval()

    def generate(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """Genera una respuesta a partir de mensajes tipo chat."""

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated_tokens = outputs[0][
            inputs["input_ids"].shape[1]:
        ]

        return self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()