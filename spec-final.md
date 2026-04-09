# **SPEC — AI Product Hackathon**

**Nhóm:** Nhóm 01_E402  
**Track:** XanhSM  
**Problem statement (1 câu):** _Người dùng đang di chuyển hoặc bận tay phải mất 30–60 giây để đặt xe thủ công; AI voice có thể hiểu ý định và tự điền form đặt xe trong \<5 giây, giảm friction và tăng conversion._

## **1\. AI Product Canvas** (Phạm Đoàn Phương Anh-2A202600257)

|             | Value                                                                                                                                                                                    | Trust                                                                                                                                             | Feasibility                                                                                                                                               |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Câu hỏi** | User nào? Pain gì? AI giải gì?                                                                                                                                                           | Khi AI sai thì sao? User sửa bằng cách nào?                                                                                                       | Cost/latency bao nhiêu? Risk chính?                                                                                                                       |
| **Trả lời** | _Người dùng đang di chuyển (đi bộ, mang đồ, vội). Pain: phải mở app, nhập địa chỉ mất 30–60s. AI: nhận voice → hiểu intent → auto-fill điểm đi/đến, loại phương tiện → giảm xuống \<5s._ | _Sai điểm đến \= cost cao (tiền \+ thời gian). → Luôn hiển thị map preview \+ địa chỉ trước khi "Accept". User sửa bằng: edit text hoặc nói lại._ | _Latency \<2s (speech-to-text \+ NLU \+ fetch data). Cost thấp (voice \+ LLM \+ API). Risk: noise → nhận sai, ambiguity ("quán phở"), location mismatch._ |

**Automation hay augmentation?** Augmentation

**Justify:**  
_Cost of error rất cao (đặt nhầm xe → mất tiền thật), nên AI chỉ gợi ý (auto-fill), user là người quyết định cuối cùng. Cost of reject ≈ 0\._

### **Learning signal**

1. **User correction đi vào đâu?**  
   → Log lại:
   - Voice input ban đầu
   - Output AI (địa chỉ dự đoán)
   - Địa chỉ user sửa lại  
     → Dùng để fine-tune:
   - Entity extraction (địa điểm)
   - User-specific mapping ("nhà tôi", "công ty")
2. **Product thu signal gì để biết tốt lên hay tệ đi?**
   - % Accept ngay (không sửa)
   - % User edit destination
   - Time-to-book (↓ là tốt)
   - Drop-off sau khi AI suggest (↑ là xấu)
3. **Data thuộc loại nào?**  
   ☑ User-specific (nhà, công ty)  
   ☑ Real-time (GPS)  
   ☑ Human-judgment (accept / sửa)  
   ☑ Domain-specific (địa điểm phổ biến)

**Marginal value:** Rất cao  
→ Model chung KHÔNG biết "nhà tôi là đâu" → càng dùng càng tốt (data moat mạnh)

## **2\. User Stories — 4 paths** (Nguyễn Đức Dũng - 2A202600148)

### **Feature: Voice → Auto-fill booking**

**Trigger:** User mở app hoặc dùng quick button → nói "Đặt xe về nhà"

| Path                           | Câu hỏi thiết kế                       | Mô tả                                                                                                                      |
| ------------------------------ | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Happy — AI đúng, tự tin        | User thấy gì? Flow kết thúc ra sao?    | AI hiểu "nhà tôi" → lấy từ profile → fill điểm đến \+ GPS hiện tại → hiển thị map → user nhấn "Accept" → đặt xe thành công |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? | User có 2 địa chỉ "nhà" → UI hiển thị: "Bạn muốn về Nhà riêng hay Nhà bà ngoại?" \+ map preview → user chọn                |
| Failure — AI sai               | User biết AI sai bằng cách nào?        | AI chọn sai địa chỉ → map hiển thị vị trí lạ → user nhận ra → không nhấn Accept                                            |
| Correction — user sửa          | User sửa bằng cách nào?                | User click vào ô destination để sửa hoặc nói lại → system log correction → cải thiện model                                 |

### **Feature: Voice → Known location (Home/Work)**

**Trigger:** User nói "Về nhà" / "Đến công ty"

| Path           | Câu hỏi thiết kế                                                                           | Mô tả                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Happy          | Làm sao map chính xác “nhà”/“công ty” với user profile? Có cần onboarding trước không?     | AI lấy địa chỉ “Home/Work” từ profile → auto-fill điểm đến → hiển thị map → user Accept |
| Low-confidence | Nếu user có nhiều địa chỉ (vd: 2 “nhà”), hỏi lại như thế nào để nhanh nhất mà không phiền? | Hiển thị 2 lựa chọn: “Nhà riêng” / “Nhà bà ngoại” → user chọn                           |
| Failure        | Nếu AI map sai “nhà” thì user nhận ra bằng cách nào?                                       | Map preview \+ địa chỉ text → user thấy lạ → không Accept                               |
| Correction     | User sửa “nhà” như thế nào? Có update lại profile không?                                   | User edit địa chỉ → system hỏi “Lưu làm nhà mới?” → cập nhật                            |

## **3\. Eval metrics \+ threshold** ( Nguyễn Đức Trí - 2A202600394)

**Optimize:** Precision

**Tại sao:**  
→ Sai điểm đến \= mất tiền thật → UX cực tệ  
→ Thà không suggest còn hơn suggest sai

**Nếu chọn sai (optimize recall):**  
→ AI đoán nhiều nhưng sai nhiều → user mất trust → bỏ feature

| Metric                         | Threshold | Red flag (dừng khi) |
| ------------------------------ | --------- | ------------------- |
| Accuracy (địa điểm quen thuộc) | ≥ 90%     | \< 75%              |
| Accept rate (no edit)          | ≥ 70%     | \< 50%              |
| Latency (voice → UI)           | \< 2s     | \> 3s               |
| Correction rate                | ≤ 20%     | \> 40%              |
| Drop-off sau suggest           | ≤ 10%     | \> 25%              |

## **4\. Top 3 failure modes** (Trương Minh Tiền - 2A202600438)

| \#  | Trigger                               | Hậu quả                               | Mitigation                                   |
| --- | ------------------------------------- | ------------------------------------- | -------------------------------------------- |
| 1   | Noise (môi trường ồn)                 | Speech-to-text sai → sai địa điểm     | Confidence threshold → nếu thấp thì hỏi lại  |
| 2   | Ambiguous intent ("quán phở")         | Chọn sai địa điểm xa                  | Hiển thị top 3 \+ hỏi rõ                     |
| 3   | Sai nhưng tự tin cao (nguy hiểm nhất) | User không để ý → đặt nhầm → mất tiền | Luôn hiển thị map preview \+ yêu cầu confirm |

**Nguy hiểm nhất:** Sai nhưng user KHÔNG biết  
→ Fix bằng: visual map \+ địa chỉ rõ ràng trước khi accept

## **5\. ROI 3 kịch bản**(Huỳnh Thái Bảo-2A202600373)

|                | Conservative        | Realistic                             | Optimistic                     |
| -------------- | ------------------- | ------------------------------------- | ------------------------------ |
| **Assumption** | 10% user dùng voice | 30% user dùng                         | 60% user dùng                  |
| **Cost**       | $30/ngày            | $100/ngày                             | $300/ngày                      |
| **Benefit**    | Giảm CSKH xử lý lỗi | \+15% booking khi user đang di chuyển | \+Retention \+ habit formation |
| **Net**        | \~ hòa vốn          | Lợi nhuận dương                       | Flywheel mạnh                  |

**Kill criteria:**

- Accept rate \<50% sau 2 tháng
- Correction rate \>40%
- User không dùng voice (\>80% ignore)

## **6\. Mini AI spec (1 trang)**

Đây là một sản phẩm AI voice assistant cho XanhSM giúp người dùng đặt xe nhanh khi đang di chuyển hoặc bận tay. Thay vì phải mở app và nhập địa chỉ thủ công, người dùng chỉ cần nói một câu như “đặt xe về nhà”, hệ thống sẽ tự động hiểu ý định, lấy dữ liệu từ user profile (địa chỉ nhà, công ty) và GPS hiện tại để điền sẵn form đặt xe.

Sản phẩm được thiết kế theo hướng **augmentation**, không phải automation. AI không tự đặt xe mà chỉ gợi ý và hiển thị đầy đủ thông tin (map, địa chỉ) để người dùng xác nhận. Điều này cực kỳ quan trọng vì cost of error cao — một quyết định sai có thể khiến user mất tiền thật.

Về chất lượng, hệ thống ưu tiên **precision hơn recall**. Nghĩa là chỉ gợi ý khi đủ chắc chắn, còn nếu không sẽ hỏi lại hoặc đưa ra nhiều lựa chọn. Các tình huống ambiguity như “quán phở” sẽ được xử lý bằng cách hiển thị danh sách gần nhất thay vì đoán bừa.

Rủi ro chính gồm:

- Noise môi trường → nhận diện sai giọng nói
- Ambiguity trong địa điểm
- Sai nhưng tự tin cao (dangerous failure)

Các rủi ro này được giảm bằng:

- Confidence threshold
- UI hỏi lại
- Map preview bắt buộc trước khi accept

Data flywheel là điểm mạnh của sản phẩm. Càng nhiều user dùng, hệ thống càng hiểu rõ:

- “nhà tôi” là đâu
- user hay đi đâu
- mapping giữa ngôn ngữ tự nhiên và địa điểm

Từ đó, trải nghiệm ngày càng nhanh và chính xác hơn, tạo lợi thế cạnh tranh dài hạn cho XanhSM.
