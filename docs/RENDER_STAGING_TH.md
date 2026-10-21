# Render staging: สถานะจริงและขั้นตอนเปิดใช้งาน

ผู้ก่อตั้งยืนยัน workspace **My Workspace — totnui555@gmail.com** แล้ว (tea-dbbj2qbbc2fs73bcelb0) งบ **100 USD เป็นงบ OpenRouter เท่านั้น** ไม่ใช่การอนุมัติงบโฮสต์รายเดือน จึงยังไม่มีการสร้าง compute แบบเสียเงิน

## สถานะล่าสุด — 21 ตุลาคม 2026

ผู้ก่อตั้งเชื่อม GitHub และใช้ Blueprint แล้ว เว็บทดลอง **https://company-os-staging-38tn.onrender.com** เปิดจริงบนแผน Free ใน Singapore (srv-dbc18bpsrm7s7399skdg) หน้า HTTPS และ /api/health ตอบ 200 และรายงาน PostgreSQL ก่อนอัปเดตดีไซน์ใหม่ ไม่ได้ย้ายข้อมูลจากเครื่องพัฒนาไปเว็บ และไม่ใช้บัญชีเจ้าของในเครื่องพัฒนาแทนบัญชีที่ผู้ก่อตั้งตั้งเองบนเว็บ

ข้อมูลการเตรียมและอุปสรรคด้านล่างเป็นประวัติก่อนเปิดเว็บ; ตอนนี้ผ่านขั้นตอนเชื่อม repository แล้ว ส่วน worker อัตโนมัติยังไม่ได้ deploy ใน free staging

## สร้างแล้ว

PostgreSQL **company-os-staging-db**, plan **free**, region **Singapore**, PostgreSQL 17, ID dpg-dbbj5h0u01pc73dvnm5g-a สถานะ available หมดอายุ **19 พฤศจิกายน 2026** บัญชีนี้ยังไม่มี web service ก่อนเริ่มงาน ไม่ได้เปลี่ยนทรัพยากรของโปรเจกต์อื่น

## โค้ดที่เตรียมแล้ว

`render.yaml` สร้างเว็บ staging แบบ free เพียงบริการเดียว และอ้างฐานข้อมูลที่สร้างแล้วด้วย `fromDatabase` จึงไม่ต้องเปิดเผยรหัสฐานข้อมูลให้แชต ไม่ประกาศฐานข้อมูลซ้ำใน Blueprint ส่วน SESSION_SECRET และ BOOTSTRAP_TOKEN ให้ Render สุ่มค่าเอง ไม่มี secret ใน Git

`infrastructure/staging.Dockerfile` รวม Next.js standalone กับ FastAPI แบบ non-root ส่วน supervisor ทำ migrations/seed ก่อนเปิดบริการ ส่งต่อสัญญาณปิด และปิดทั้งคู่หากโปรเซสใดล้ม ไม่รัน Temporal/scheduler/worker ใน free web container

โค้ดรองรับ PostgreSQL URL ของผู้ให้บริการผ่านไดรเวอร์ psycopg ที่ติดตั้งจริง, Temporal Cloud API key บน TLS, private host:port สำหรับ proxy และค่าใช้จ่ายต่ำกว่าหนึ่งบาทที่ไม่ถูกปัดแสดงเป็นศูนย์ หน้า staging แสดงข้อจำกัดของ environment อย่างชัดเจน

## ตรวจแล้ว / ยังไม่ตรวจ

- Backend ล่าสุด 79 tests ผ่าน รวม PostgreSQL/Temporal จริง; frontend 15 tests, typechecks และ production build ผ่าน
- Native staging process smoke ผ่าน: migrations, PostgreSQL, Next standalone, same-origin proxy, owner login, 25 roles, audit chain และ graceful shutdown โดยใช้ฐานข้อมูล integration test แยกจากข้อมูลจริง
- Blueprint ผ่าน JSON Schema ทางการปัจจุบัน
- ติดตั้ง Render CLI v2.30.0 จาก release ทางการพร้อมตรวจ SHA-256 แต่ platform validation ต้อง login CLI เพิ่ม การเชื่อม OAuth ของ connector ไม่ใช่ credential ที่ส่งต่อให้ CLI ได้
- **ณ checkpoint เตรียมระบบเดิมยังไม่มี Render web deployment** ต่อมาผู้ก่อตั้งเปิดจริงสำเร็จตามสถานะล่าสุดด้านบน; การทดสอบ process ในเครื่องยังคงไม่ใช้แทนการยืนยัน hosted deployment

## ขั้นตอนใน Dashboard ที่เหลือ

เปิด https://dashboard.render.com/blueprint/new?repo=https://github.com/totnui555-commits/Codex-2

1. ใช้ workspace My Workspace และเชื่อม GitHub repository หาก Render ขอสิทธิ์อ่าน repo ส่วนตัว
2. เลือก branch **codex/company-os-implementation**, Blueprint Path **render.yaml** (default branch main ยังเป็นฐาน review จึงไม่พบไฟล์นี้)
3. ตรวจรายการว่ามี **company-os-staging / Free** และอ้างฐานข้อมูล **company-os-staging-db** เดิม ไม่สร้างฐานข้อมูลฟรีซ้ำ ไม่เลือก paid plan
4. ให้ Dashboard ตรวจ Blueprint แล้วกด Deploy Blueprint จากนั้นผู้ดำเนินการตรวจ deploy ID จนเป็น live และทดสอบ HTTPS/login/persistence อีกครั้ง จึงจะยืนยันว่าเปิดใช้สำเร็จ
5. การตั้ง owner ครั้งแรกใช้ BOOTSTRAP_TOKEN จาก secure Render environment และรหัสผ่านที่เจ้าของกำหนดเอง ผ่าน bootstrap API ที่ป้องกันด้วย token ห้ามส่งค่า secret ในอีเมลหรือใส่ลง Git

ขั้นตอน Dashboard นี้เป็นข้อจำกัดของช่องทางเชื่อมต่อปัจจุบัน ไม่ใช่การขออนุญาตครอบคลุมซ้ำ Render MCP สร้างทรัพยากรบางชนิดได้ แต่ไม่สร้าง Blueprint และไม่รองรับการตั้งค่า `fromDatabase` ในคำสั่งสร้างเว็บ ส่วน fresh headless browser ไม่มี authenticated Dashboard session

## ขอบเขต staging

Free web sleeps หลังไม่มีคนใช้และไม่ใช่ runtime 24/7 ฐานข้อมูลฟรีมีอายุ 30 วันและไม่มี managed backup ห้ามเก็บ production/customer data หรือย้ายข้อมูลจริงจาก workspace ไปโดยถือเป็น backup ไม่มี OpenRouter key, Daytona key, email OAuth หรือ billing secret ถูกส่งไปยัง staging แผนนี้ไม่แทน hardened hosted coding benchmark หรือ production release gate

Production ยังต้องมีงบโฮสต์แยก, role-scoped PostgreSQL connections, production Temporal, private object storage, worker/scheduler/Watchtower แยกบริการ, Daytona และ deployment verification ที่ผ่านจริง


## ตรวจซ้ำหลังผู้ก่อตั้งสั่งเปิดเว็บ — 20 ตุลาคม 2026

Connector ปัจจุบันรองรับ Docker web creation แล้ว จึงลองสร้าง company-os-staging / Free / Singapore จาก branch ที่มีโค้ดล่าสุดโดยตรง ผลจริงคือ HTTP 400: repository URL invalid or unfetchable. GitHub ยืนยันว่า repository เป็น PRIVATE และ Render ยังไม่มี web service หลังคำสั่งดังกล่าว จึงยังไม่มี public URL ที่ใช้งานได้ และไม่อ้างว่าการ deploy สำเร็จ

สิ่งที่ต้องทำในบัญชีเจ้าของคืออนุญาต Render GitHub App อ่าน Codex-2 แล้วใช้ Blueprint ตามขั้นตอนด้านบน เพื่อผูกฐานข้อมูลเดิมโดยไม่เปิดเผย connection string. เครื่องมือที่เชื่อมอยู่ไม่มี authenticated Dashboard browser หรือ Blueprint apply capability; จึงทำ GitHub OAuth แทนเจ้าของไม่ได้ ไม่มีการเปลี่ยน repository เป็น public หรือสร้าง paid service.


อัปเดตดีไซน์ทั่วไปสำเร็จ: deployment dep-dbc2440n74is73f3n4rg / commit f4dce7d เป็น live แล้ว ตรวจ login แบบใหม่, CSS, PostgreSQL health และการป้องกัน snapshot ที่ยังไม่ล็อกอินผ่านจริง ดู system-console-hosted-browser.json และ system-console-deployment.json ใน docs/evidence. ใช้บัญชีที่ตั้งบนเว็บนี้เอง; ไม่มีการนำรหัสผ่าน/ข้อมูลเจ้าของจากเครื่องพัฒนาไปใส่ใน staging
