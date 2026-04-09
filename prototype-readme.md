# Prototype — XanhSM AI Voice Assistant

## Mô tả

Hệ thống AI Voice Assistant giúp người dùng đặt xe XanhSM siêu tốc bằng giọng nói. Hệ thống tự động nhận diện ý định (intent), trích xuất thực thể địa điểm (entity extraction) và đối soát với dữ liệu cá nhân (Home/Work) để điền sẵn form đặt xe kèm Map preview.

## Level: Mock prototype

### 1. Sketch

- **UI/UX Flow:** Phác thảo luồng tương tác: Nhấn giữ Mic -> Nói -> Hiển thị Form điền sẵn -> Xác nhận đặt xe.
- **Logic:** Xác định các trường hợp ngoại lệ (Failure modes) như địa chỉ không rõ ràng hoặc chưa lưu địa chỉ nhà/công ty.

### 2. Mock

- **Data:** Sử dụng `users.json` để giả lập Profile người dùng.
- **UI:** Giao diện mô phỏng ứng dụng XanhSM build bằng **Expo (React Native)** với các thành phần tĩnh cho Map.

### 3. Working

- **Frontend (FE):** Ứng dụng Expo chạy trên thiết bị thật, tích hợp **OpenAI Whisper (STT)** để chuyển đổi giọng nói thành văn bản. FE gửi chuỗi văn bản và tọa độ GPS hiện tại lên hệ thống.
- **AI Agent (The Interpreter)**: Sử dụng các mô hình ngôn ngữ lớn (LLM) như Gemini đóng vai trò là AI Agent, giúp phân tích ngữ cảnh và bóc tách các thực thể (Entities) từ văn bản/giọng nói. Hệ thống có khả năng nhận diện chính xác các tham số như: Điểm xuất phát (Pickup), Đích đến (Destination), và Loại phương tiện (Vehicle Type). Kết quả được chuẩn hóa thành cấu trúc JSON để Backend thực hiện logic đối soát dữ liệu cá nhân và tính toán lộ trình.

- **Backend (BE - The Orchestrator & Decision Maker):** - Hệ thống **FastAPI** tiếp nhận thực thể từ Agent và thực hiện logic ra quyết định: - Đối soát thực thể với dữ liệu cá nhân trong `users.json` (Saved locations). - Nếu không có trong dữ liệu cá nhân, tự động kích hoạt **Tool Map (Geopy)** để tìm kiếm địa chỉ thực tế.
  - Tính toán quãng đường di chuyển bộ thực tế qua **OSRM API**.
  - Tổng hợp thông tin và trả về gói dữ liệu hoàn chỉnh cho Mobile App.
- **Map Integration:** Kết nối trực tiếp Geopy và OSRM để đảm bảo tính xác thực của vị trí và giá tiền.

## Links

- **Prototype (UI/Demo):** []
- **Prompt test log:** [https://drive.google.com/drive/folders/1vsnRai7hlYO_0JxA_5xtwcOgVIgQApmh?usp=drive_link]
- **Video demo (backup):** [https://drive.google.com/drive/folders/1qPSRlRhL8OANuXyDrGkJgamyHAQFWu3q?usp=sharing]

## Tools

- **Framework:** FastAPI, Uvicorn.
- **AI/NLU:** OpenAI speech model (Local), Gemini (API) for Agent, LangChain/ Langgraph (dựa trên bối cảnh dự án).
- **Map API:** Geopy (Geocoding), OSRM (Routing).
- **Voice (Dự kiến):** OpenAI Whisper cho STT (Speech-to-Text).

## Phân công (Dựa trên Spec Nhóm 01_E402)

| Thành viên           | Phần                              | Output               |
| :------------------- | :-------------------------------- | :------------------- |
| Phạm Đoàn Phương Anh | Canvas + Learning Signal          | spec-final.md phần 1 |
| Nguyễn Đức Dũng      | User stories + Prompt Engineering | spec-final.md phần 2 |
| Nguyễn Đức Trí       | Eval metrics + Threshold          | spec-final.md phần 3 |
| Trương Minh Tiền     | Failure modes + Mitigation        | spec-final.md phần 4 |
| Huỳnh Thái Bảo       | ROI + Kill criteria               | spec-final.md phần 5 |
