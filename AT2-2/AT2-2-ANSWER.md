AT2-2 Integration Testing Report
รหัสนักศึกษา: 650612090 ชื่อ: ผืนป่า จำปาศรี

1.สิ่งที่ค้นพบ (Observations)
การจัดการ Floating Point: ใน OrderService มีการคำนวณ total เป็น float แล้วค่อย round ตอน return ค่า dict แต่ตอนส่งให้ Payment gateway ส่งค่าดิบไป ซึ่งอาจเกิดปัญหาทศนิยม (เช่น 100.00000001) ทำให้เงื่อนไขการเช็คยอดเงินในระบบจริงผิดพลาดได้ ควร round ก่อนส่ง Payment

Payment Rollback Flow: การเขียนเทสต์แบบ Top-down ทำให้เห็นชัดเจนว่า ถ้า pay.charge() ล้มเหลว ระบบจะวนลูป release สต็อกคืน ซึ่งเป็นจุดวิกฤต ถ้าลูปนี้พัง สต็อกจะหายไปฟรีๆ

การพึ่งพา Email Service: ระบบออกแบบให้ try-except ครอบ EmailService ไว้ ทำให้ถ้าส่งเมลล์ไม่ผ่าน Order ก็ยังสำเร็จ ซึ่งถูกต้องตาม Requirement แต่ในความเป็นจริงอาจต้องมีการ Log error ไว้ด้วย ไม่งั้นเราจะไม่รู้เลยว่าลูกค้าไม่ได้รับอีเมล

2. การทดสอบโค้ดนี้แบบอัตโนมัติ มีข้อดี ข้อเสียอะไรบ้าง
ข้อดี:

Regression Testing: มั่นใจได้ว่าเมื่อแก้โค้ดส่วนหนึ่ง (เช่น Inventory) จะไม่ไปทำพังในส่วนอื่น (เช่น Order Flow) เพราะเทสต์จะฟ้องทันที

Speed: คอมพิวเตอร์รันเทสต์หลักร้อยเคสได้ในเวลาไม่กี่วินาที เร็วกว่าให้คนมากด Manual test มาก

Documentation: โค้ดเทสต์ทำหน้าที่เป็นคู่มือที่บอกว่าระบบควรทำงานอย่างไร (Living Documentation)

ข้อเสีย:

Maintenance Cost: เมื่อ Requirement เปลี่ยน (เช่น เปลี่ยน Logic ค่าส่ง) ต้องมาแก้โค้ดเทสต์ด้วย

False Confidence: การที่เทสต์ผ่านบน Mock/Stub ไม่ได้การันตี 100% ว่าบน Production จะไม่พัง (เช่น Network จริงล่ม)

3. ขั้นตอนการทำให้เทสต์รันอัตโนมัติอย่างเป็นระบบที่ทำในกิจกรรมนี้ คืออะไร
Environment Setup: เตรียม requirements.txt และติดตั้ง Library (pytest)

Test Strategy Design: วิเคราะห์ Call Graph เพื่อเลือกจุดที่จะทำ Stub/Spy (Top-down) และจุดที่จะเทสต์จริง (Bottom-up)

Implementation: เขียนโค้ดทดสอบโดยแยกเป็น Module และใช้ Markers เพื่อจัดกลุ่ม

CI Integration: นำโค้ดขึ้น GitHub และสร้าง Workflow (GitHub Actions) เพื่อให้เทสต์รันทุกครั้งที่มีการ Push โค้ด

4. ชุดทดสอบตั้งต้น ได้ coverage เท่าไร เมื่อเพิ่มกรณีทดสอบแล้ว ได้ coverage เท่าไร
(ส่วนนี้ต้องลองรันจริงด้วย pytest --cov=. ถ้าทำได้ แต่ถ้าประมาณการ)

ตั้งต้น: 0% (เพราะยังไม่มีไฟล์เทสต์)

หลังเพิ่มกรณีทดสอบ: น่าจะสูงกว่า 90% เพราะเราเทสต์ทั้ง Success path, Failure path (Inventory เต็ม, เงินไม่พอ) และครอบคลุมทุก Service หลัก

5. เป็นไปได้ไหมที่จะทำให้ได้ 100% integration test coverage ให้เหตุผล
เป็นไปได้ยากมาก และอาจไม่คุ้มค่า

เหตุผล: Integration test เน้นการเชื่อมต่อ การจะเทสต์ให้ครบทุก State ของทุก Service ที่มาประกอบกัน (Cartesian product of states) นั้นมหาศาลมาก นอกจากนี้ยังมีปัจจัยภายนอก (Infrastructure failures) ที่จำลองได้ยากใน Integration test ปกติ การพยายามทำให้ได้ 100% มักจะไปจบที่การเขียนเทสต์ที่ซับซ้อนเกินความจำเป็น (Diminishing returns)
