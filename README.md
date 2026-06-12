# KET/PET/FCE Vocabulary Story Lab

基于 KET / PET / FCE 分级词汇的英语阅读与 Worksheet 自测网站。

## 功能

- 按 KET / PET / FCE 选择词汇等级。
- 支持两种内容模式：低龄绘本故事、标准考级阅读文章。
- 自动生成随文绑定 Worksheet：词义匹配、选词填空、阅读理解、True/False、句型改写。
- 在线提交后自动批改，输出得分、正确率、评级、错题解析和薄弱词汇。
- 融合 L1-L8 外教主修课大纲理念：生活主题、自然拼读、学习周期测试、文本特征、推断评价、观点表达和写作输出。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```

打开 http://127.0.0.1:8000

## 图片生成 API

阅读页配图会调用 ImaRouter / OpenAI-compatible Images API。不要把真实 Key 写进代码或提交到 Git。

```powershell
$env:IMAROUTER_API_KEY="your_api_key_here"
$env:IMAGE_API_URL="https://api.imarouter.com/v1/images/generations"
$env:IMAGE_MODEL="gpt-image-2"
uvicorn app:app --reload
```

可选配置：

- `IMAGE_API_URL`：默认 `https://api.imarouter.com/v1/images/generations`
- `IMAGE_MODEL`：默认 `gpt-image-2`
- `IMAGE_SIZE`：默认 `1024x1024`

ImaRouter 的 `gpt-image-2` 生图接口是异步任务：后端会先提交生成请求，再自动轮询 `GET /v1/images/generations/{task_id}`，成功后把图片 URL 返回给前端。

## 说明

当前版本使用本地词汇驱动生成引擎，确保内容严格绑定 KET/PET/FCE 三套词库。后续可在 `app.py` 的生成函数中接入真实 LLM API，但仍应保留词库约束与服务端批改答案。
