# FF Tool - Free Fire Account Manager

## Deploy lên Render

1. Push toàn bộ code lên GitHub
2. Vào [render.com](https://render.com) → **New Web Service**
3. Kết nối với repo GitHub của bạn
4. Render sẽ tự detect các cài đặt từ `render.yaml`
5. Nhấn **Deploy**

## Cấu trúc thư mục

```
ff_tool/
├── app.py
├── core.py
├── bot_.py
├── MajorLoginRes_pb2.py
├── requirements.txt
├── render.yaml
├── Procfile
└── templates/
    └── index.html
```

## Chạy local

```bash
pip install -r requirements.txt
python app.py
```

Truy cập: http://localhost:5000
