import os
import asyncio
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# System prompt for the AI assistant
SYSTEM_PROMPT = """你是一个亲切友好的社区安全知识助手。你的任务是：
1. 用温暖、通俗易懂的语气向社区居民（老人、小孩、成年人）普及安全应急知识。
2. 回答要简洁，每条不超过300字。
3. 可以使用emoji让回答更生动，但不要过度。
4. 适合讲解的主题包括：
   - 消防安全（火灾预防、灭火器使用、逃生技巧）
   - 地震/自然灾害避险
   - 急救知识（CPR、止血、烧伤处理）
   - 日常安全（用电安全、防溺水、防诈骗）
5. 如果问题超出安全知识范围，请委婉地引导回安全话题。
"""


def get_minimax_client():
    """Get MiniMax API client (OpenAI-compatible format)"""
    from openai import OpenAI
    return OpenAI(
        api_key=os.getenv("MINIMAX_API_KEY"),
        base_url="https://api.minimax.chat/v1",
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"reply": "请输入您的问题，我会尽力回答！"})

    try:
        client = get_minimax_client()
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        # 过滤掉think标签内容
        import re
        reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"抱歉，服务出错了。请稍后再试。错误信息：{str(e)}"}), 500


@app.route("/api/tts", methods=["POST"])
def tts():
    """使用edge-tts生成自然语音"""
    import edge_tts
    import re

    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "文本不能为空"}), 400

    # 清理文本，移除markdown格式
    text = re.sub(r'#+ ', '', text)  # 移除标题标记
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # 移除加粗
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # 移除斜体
    text = re.sub(r'- ', '', text)  # 移除列表标记
    text = re.sub(r'\n+', ' ', text)  # 换行变空格
    text = re.sub(r'\s+', ' ', text)  # 多个空格变一个

    async def generate_audio():
        try:
            # 使用微软晓晓语音，中文女声，非常自然
            communicate = edge_tts.Communicate(
                text,
                voice="zh-CN-XiaoxiaoNeural",
                rate="+10%",  # 稍微加快语速，更自然
                volume="+0%"   # 正常音量
            )
            await communicate.save("/tmp/safety_tts_audio.mp3")
        except Exception as e:
            print(f"TTS error: {e}")

    try:
        asyncio.run(generate_audio())
        # 读取生成的音频文件
        with open("/tmp/safety_tts_audio.mp3", "rb") as f:
            audio_data = f.read()
        # 删除临时文件
        os.remove("/tmp/safety_tts_audio.mp3")
        # 返回音频
        return Response(
            audio_data,
            mimetype="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=audio.mp3"}
        )
    except Exception as e:
        return jsonify({"error": f"TTS生成失败: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
