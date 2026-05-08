// helpers/api/authEvents.ts
import { EventEmitter } from "eventemitter3";
export const authEvents = new EventEmitter();
export const AUTH_EXPIRED_EVENT = "auth_expired";
