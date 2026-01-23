# Multi-Agent Intelligence Platform - Test Cases

> คู่มือการทดสอบระบบสำหรับ Tester แบบ Step-by-Step

**Environment:** `http://localhost` (Docker Production)  
**Version:** 1.1.0  
**Last Updated:** January 23, 2026

---

## 📋 สารบัญ

1. [เตรียมสภาพแวดล้อม](#1-เตรียมสภาพแวดล้อม)
2. [TC-AUTH: ทดสอบ Authentication](#2-tc-auth-ทดสอบ-authentication)
3. [TC-CHAT: ทดสอบ Chat & WebSocket](#3-tc-chat-ทดสอบ-chat--websocket)
4. [TC-ADMIN: ทดสอบ Admin Panel](#4-tc-admin-ทดสอบ-admin-panel)
5. [TC-AGENT: ทดสอบ Agent Management](#5-tc-agent-ทดสอบ-agent-management)
6. [TC-TOOL: ทดสอบ Tool Approval](#6-tc-tool-ทดสอบ-tool-approval)
7. [TC-API: ทดสอบ REST API](#7-tc-api-ทดสอบ-rest-api)
8. [TC-NEG: Negative Test Cases](#8-tc-neg-negative-test-cases)
9. [TC-PERF: Performance Testing](#9-tc-perf-performance-testing)

---

## 1. เตรียมสภาพแวดล้อม

### Prerequisites Checklist

| Item | Command/Action | Expected |
|------|----------------|----------|
| Docker Desktop | เปิดโปรแกรม | Running |
| Ollama (Optional) | `ollama list` | แสดงรายการ models |
| Start Services | `docker compose -f docker-compose.prod.yml up -d --build` | Services healthy |
| Verify Backend | `curl http://localhost/api/v1/health` | `{"status": "ok"}` |
| Open Browser | Navigate to `http://localhost` | Login page แสดง |

### Test Accounts

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `admin` | `admin` | admin | All |
| `dev` | `dev` | developer | Most (no admin-only) |
| `user` | `user` | user | Basic chat only |

---

## 2. TC-AUTH: ทดสอบ Authentication

### TC-AUTH-001: Login สำเร็จ (Admin)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด `http://localhost` | แสดงหน้า Login |
| 2 | กรอก Username: `admin` | ช่อง username มีค่า |
| 3 | กรอก Password: `admin` | ช่อง password มีค่า (masked) |
| 4 | คลิกปุ่ม "Login" | ✅ Redirect ไปหน้า Chat |
| 5 | ตรวจสอบ UI | แสดงชื่อ user และปุ่ม "Admin Panel" |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-AUTH-002: Login สำเร็จ (Developer)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด `http://localhost` | แสดงหน้า Login |
| 2 | กรอก Username: `dev`, Password: `dev` | ช่องมีค่า |
| 3 | คลิกปุ่ม "Login" | ✅ Redirect ไปหน้า Chat |
| 4 | ตรวจสอบ UI | แสดงชื่อ user และปุ่ม "Admin Panel" |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-AUTH-003: Login สำเร็จ (User)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด `http://localhost` | แสดงหน้า Login |
| 2 | กรอก Username: `user`, Password: `user` | ช่องมีค่า |
| 3 | คลิกปุ่ม "Login" | ✅ Redirect ไปหน้า Chat |
| 4 | ตรวจสอบ UI | **ไม่**แสดงปุ่ม "Admin Panel" (user role) |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-AUTH-004: Login ล้มเหลว (Wrong Password)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด `http://localhost` | แสดงหน้า Login |
| 2 | กรอก Username: `admin`, Password: `wrongpassword` | ช่องมีค่า |
| 3 | คลิกปุ่ม "Login" | ❌ แสดง error message |
| 4 | ตรวจสอบ URL | ยังอยู่หน้า Login |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-AUTH-005: Login ล้มเหลว (Empty Fields)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด `http://localhost` | แสดงหน้า Login |
| 2 | ปล่อย Username/Password ว่าง | ช่องว่างเปล่า |
| 3 | คลิกปุ่ม "Login" | ❌ แสดง validation error |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-AUTH-006: Logout

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login ด้วย `admin:admin` | อยู่หน้า Chat |
| 2 | คลิกปุ่ม Logout / User menu | แสดงเมนู |
| 3 | คลิก "Logout" | ✅ Redirect ไปหน้า Login |
| 4 | กด Back button | ❌ ไม่สามารถกลับไปหน้า Chat ได้ |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

## 3. TC-CHAT: ทดสอบ Chat & WebSocket

### TC-CHAT-001: เริ่ม Conversation ใหม่

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login ด้วย `admin:admin` | อยู่หน้า Chat |
| 2 | คลิก "New Conversation" หรือเริ่มใหม่ | UI พร้อมรับ input |
| 3 | ตรวจสอบ Domain Selector | แสดงรายการ domains |
| 4 | ตรวจสอบ Agent Selector | แสดงรายการ agents ตาม domain |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-CHAT-002: ส่งข้อความและรับ Response (Streaming)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login และเตรียม Conversation | พร้อมส่งข้อความ |
| 2 | พิมพ์ข้อความ: "Hello, how are you?" | ข้อความแสดงใน input |
| 3 | กด Enter หรือคลิก Send | ✅ ข้อความ user ปรากฏใน chat |
| 4 | รอ response | ✅ ข้อความ streaming เข้ามาทีละ chunk |
| 5 | รอจนเสร็จ | ✅ แสดง response ครบถ้วน |

> **หมายเหตุ:** ถ้า Ollama ไม่พร้อม อาจได้ echo response `[AgentName] Your message`

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-CHAT-003: WebSocket Reconnection

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login และเปิด Chat | WebSocket connected |
| 2 | เปิด DevTools > Network > WS | เห็น WebSocket connection |
| 3 | Restart backend: `docker restart mai-backend` | Connection dropped |
| 4 | รอ 3-5 วินาที | ✅ WebSocket reconnect อัตโนมัติ |
| 5 | ส่งข้อความใหม่ | ✅ ทำงานได้ปกติ |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-CHAT-004: PING/PONG Keep-Alive

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login และเปิด Chat | WebSocket connected |
| 2 | เปิด DevTools > Network > WS > Messages | เห็น messages |
| 3 | รอ 30 วินาที | ✅ เห็น PING/PONG messages|
| 4 | ไม่มี reconnection หลัง idle | ✅ Connection stable |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-CHAT-005: เปลี่ยน Domain

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | อยู่หน้า Chat | พร้อมใช้งาน |
| 2 | คลิก Domain Selector | แสดง dropdown |
| 3 | เลือก domain อื่น | ✅ Agent list อัปเดตตาม domain |
| 4 | ส่งข้อความ | ✅ Response มาจาก agent ใน domain ใหม่ |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

## 4. TC-ADMIN: ทดสอบ Admin Panel

### TC-ADMIN-001: เข้า Admin Panel

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login ด้วย `admin:admin` | อยู่หน้า Chat |
| 2 | คลิกปุ่ม "Admin Panel" | ✅ Redirect ไป Admin Page |
| 3 | ตรวจสอบ tabs | เห็น 5 tabs: Overview, Domains, Agents, Tools, Settings |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-ADMIN-002: Overview Tab - StatCards

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เข้า Admin Panel > Overview tab | แสดง Overview |
| 2 | ตรวจสอบ StatCards | เห็น 4 cards: Domains, Agents, Conversations, Pending Tools |
| 3 | ตรวจสอบค่าตัวเลข | ค่าเป็นตัวเลข ≥ 0 |
| 4 | ตรวจสอบ icons | แต่ละ card มี icon |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-ADMIN-003: Overview Tab - Auto Refresh

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เข้า Admin Panel > Overview | แสดง metrics |
| 2 | เปิด DevTools > Network | เห็น requests |
| 3 | รอ 5 วินาที | ✅ เห็น request ใหม่ไป `/metrics` |
| 4 | สร้าง conversation ใหม่ในอีก tab | - |
| 5 | รอ 5 วินาที | ✅ Conversations count เพิ่มขึ้น |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-ADMIN-004: Domains Tab - List

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เข้า Admin Panel > Domains tab | แสดงรายการ domains |
| 2 | ตรวจสอบข้อมูล | เห็น domain ID, name, agent count |
| 3 | พิมพ์ค้นหาใน search box | ✅ Filter ทำงาน |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-ADMIN-005: Domains Tab - Detail

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | อยู่ Domains tab | เห็นรายการ |
| 2 | คลิกเลือก domain | ✅ แสดง detail panel ด้านขวา |
| 3 | ตรวจสอบ detail | เห็น description, agents list, routing rules |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-ADMIN-006: Agents Tab - List & Filter

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เข้า Admin Panel > Agents tab | แสดงรายการ agents |
| 2 | ตรวจสอบข้อมูล | เห็น agent ID, name, version, state badge |
| 3 | เลือก filter by domain | ✅ แสดง agents ตาม domain |
| 4 | เลือก filter by state | ✅ แสดง agents ตาม state |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-ADMIN-007: Agents Tab - State Badge Colors

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | อยู่ Agents tab | เห็นรายการ |
| 2 | ตรวจสอบ state badges | DEVELOPMENT = สีน้ำเงิน/neutral |
| 3 | | TESTING = สีเหลือง/warning |
| 4 | | PRODUCTION = สีเขียว/success |
| 5 | | DEPRECATED = สีส้ม/warning |
| 6 | | ARCHIVED = สีเทา/disabled |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

## 5. TC-AGENT: ทดสอบ Agent Management

### TC-AGENT-001: View Agent Detail

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เข้า Admin > Agents tab | เห็นรายการ |
| 2 | คลิกเลือก agent | ✅ แสดง detail panel |
| 3 | ตรวจสอบ info | เห็น: ID, Name, Description, Model, State, Version |
| 4 | ตรวจสอบ tools list | เห็นรายการ tools ที่ agent ใช้ได้ |
| 5 | ตรวจสอบ capabilities | เห็นรายการ capabilities |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-AGENT-002: Promote Agent State

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เลือก agent ที่ state = DEVELOPMENT | แสดง detail |
| 2 | หาปุ่ม "Promote" หรือ state buttons | เห็นปุ่ม |
| 3 | คลิก Promote to TESTING | ✅ State เปลี่ยนเป็น TESTING |
| 4 | คลิก Promote to PRODUCTION | ✅ State เปลี่ยนเป็น PRODUCTION |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-AGENT-003: Demote/Archive Agent

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เลือก agent ที่ state = PRODUCTION | แสดง detail |
| 2 | คลิก Deprecate | ✅ State เปลี่ยนเป็น DEPRECATED |
| 3 | คลิก Archive | ✅ State เปลี่ยนเป็น ARCHIVED |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

## 6. TC-TOOL: ทดสอบ Tool Approval

### TC-TOOL-001: View Tool Runs List

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เข้า Admin Panel > Tools tab | แสดงรายการ tool runs |
| 2 | ตรวจสอบข้อมูล | เห็น: Tool ID, Status, Created time |
| 3 | Filter by status = pending | ✅ แสดงเฉพาะ pending |
| 4 | Filter by status = approved | ✅ แสดงเฉพาะ approved |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-TOOL-002: Approve Tool Run

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | หา tool run ที่ status = pending | เห็นรายการ |
| 2 | คลิกปุ่ม "Approve" | ✅ แสดง confirmation modal |
| 3 | ยืนยัน Approve | ✅ Status เปลี่ยนเป็น approved |
| 4 | รอ execution | ✅ Status เปลี่ยนเป็น executed (ถ้า tool ทำงานสำเร็จ) |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-TOOL-003: Reject Tool Run

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | หา tool run ที่ status = pending | เห็นรายการ |
| 2 | คลิกปุ่ม "Reject" | ✅ แสดง modal พร้อมช่อง reason |
| 3 | กรอก rejection reason | ช่องมีค่า |
| 4 | คลิก Confirm Reject | ✅ Status เปลี่ยนเป็น rejected |
| 5 | ตรวจสอบ rejection reason | ✅ แสดง reason ที่กรอก |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

### TC-TOOL-004: Tool Approval Modal - View Parameters

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | คลิก View/Approve บน pending tool run | ✅ เปิด modal |
| 2 | ตรวจสอบ modal content | เห็น: Tool name, Description |
| 3 | ตรวจสอบ parameters | ✅ แสดง parameters ที่ tool จะใช้ |
| 4 | คลิก Cancel | ✅ ปิด modal ไม่มีการเปลี่ยนแปลง |

**Status:** ⬜ Pass / ⬜ Fail  
**Notes:** ________________________________________________

---

## 7. TC-API: ทดสอบ REST API

> ใช้เครื่องมือ: Postman, curl, หรือ Browser DevTools

### TC-API-001: Health Check

```bash
curl http://localhost/api/v1/health
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run command | Status 200 |
| 2 | ตรวจสอบ response | `{"status": "ok"}` |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-API-002: Health Details (Authenticated)

```bash
# Get token first
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Then call health details
curl http://localhost/api/v1/health/details -H "Authorization: Bearer $TOKEN"
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run commands | Status 200 |
| 2 | ตรวจสอบ response | เห็น auth_mode, database, version, counts |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-API-003: List Domains

```bash
curl http://localhost/api/v1/domains -H "Authorization: Bearer $TOKEN"
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run command | Status 200 |
| 2 | ตรวจสอบ response | Array of domain objects |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-API-004: List Agents

```bash
curl http://localhost/api/v1/agents -H "Authorization: Bearer $TOKEN"
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run command | Status 200 |
| 2 | ตรวจสอบ response | Array of agent objects |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-API-005: Unauthorized Access

```bash
curl http://localhost/api/v1/domains
# (no Authorization header)
```

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run command | Status 401 or 403 |
| 2 | ตรวจสอบ response | Error message |

**Status:** ⬜ Pass / ⬜ Fail

---

## 8. TC-NEG: Negative Test Cases

### TC-NEG-001: Access Admin Without Login

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Clear browser cookies/localStorage | ไม่มี session |
| 2 | เข้าตรงไปที่ `http://localhost/admin` | ❌ Redirect ไป Login |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-NEG-002: User Role Access Admin

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login ด้วย `user:user` | อยู่หน้า Chat |
| 2 | ตรวจสอบ UI | ❌ ไม่เห็นปุ่ม Admin Panel |
| 3 | พยายามเข้า `/admin` ตรงๆ | ❌ ไม่มีสิทธิ์ หรือ redirect |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-NEG-003: Send Empty Message

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | อยู่หน้า Chat | พร้อมส่งข้อความ |
| 2 | ไม่พิมพ์อะไรเลย กด Send | ❌ ไม่ส่งข้อความ หรือ validation error |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-NEG-004: Backend Down - WebSocket

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login และเปิด Chat | WebSocket connected |
| 2 | Stop backend: `docker stop mai-backend` | Connection lost |
| 3 | ตรวจสอบ UI | ✅ แสดง disconnected indicator |
| 4 | Start backend: `docker start mai-backend` | - |
| 5 | รอ reconnection | ✅ Auto reconnect |

**Status:** ⬜ Pass / ⬜ Fail

---

### TC-NEG-005: Invalid Token

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด DevTools > Application > Local Storage | เห็น token |
| 2 | แก้ไข token เป็นค่าผิด | Token corrupted |
| 3 | Refresh page | ❌ Redirect ไป Login |

**Status:** ⬜ Pass / ⬜ Fail

---

## 9. TC-PERF: Performance Testing

### TC-PERF-001: Page Load Time

| Page | Target | Actual | Status |
|------|--------|--------|--------|
| Login Page | < 2s | ___s | ⬜ |
| Chat Page | < 3s | ___s | ⬜ |
| Admin Page | < 3s | ___s | ⬜ |

---

### TC-PERF-002: WebSocket Response Time

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด DevTools > Network > WS | พร้อมวัด |
| 2 | ส่งข้อความ | - |
| 3 | วัดเวลาจาก send ถึง first chunk | < 500ms (with Ollama) |

**Status:** ⬜ Pass / ⬜ Fail  
**Actual Time:** ___ms

---

### TC-PERF-003: Concurrent Users (Optional)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | เปิด 5 browser tabs | ทั้งหมด Login |
| 2 | ส่งข้อความพร้อมกันทุก tab | ✅ ทุก tab ได้ response |
| 3 | ตรวจสอบไม่มี error | ✅ ไม่มี 500 error |

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Summary Report

### Test Execution Info

| Field | Value |
|-------|-------|
| **Tester Name** | |
| **Test Date** | |
| **Environment** | Docker Production |
| **Build Version** | |
| **Browser** | |

### Results Summary

| Category | Total | Passed | Failed | Not Run |
|----------|-------|--------|--------|---------|
| TC-AUTH | 6 | | | |
| TC-CHAT | 5 | | | |
| TC-ADMIN | 7 | | | |
| TC-AGENT | 3 | | | |
| TC-TOOL | 4 | | | |
| TC-API | 5 | | | |
| TC-NEG | 5 | | | |
| TC-PERF | 3 | | | |
| **TOTAL** | **38** | | | |

### Failed Test Details

| Test ID | Issue Description | Severity |
|---------|-------------------|----------|
| | | |
| | | |

### Notes & Observations

```
(เขียนบันทึกเพิ่มเติม)




```

---

**Approved By:** _________________________  
**Date:** _________________________
