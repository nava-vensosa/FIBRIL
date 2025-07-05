#!/usr/bin/env python3
"""
MaxMSP OSC Reception Troubleshooting Guide
"""

print("🎵 FIBRIL → MaxMSP OSC Troubleshooting")
print("=" * 40)

print("\n🔧 RECENT CHANGES MADE:")
print("  ✓ Changed from OSC bundles to individual messages")
print("  ✓ Added 1ms delay between messages")
print("  ✓ Volume values now send as integers (1/0)")

print("\n📋 MaxMSP SETUP CHECKLIST:")
print("  1. [udpreceive 1762] - Receiving UDP on correct port")
print("  2. Connect to [print] to see if ANY data is received")
print("  3. If receiving data, connect to OSC parsing objects:")
print("     [udpreceive 1762] → [print]")
print("     [udpreceive 1762] → [OSC-route voice_ active_count]")

print("\n🐛 COMMON ISSUES & SOLUTIONS:")
print("  ISSUE: No data received at all")
print("  ✓ Check port 1762 is correct in MaxMSP")
print("  ✓ Make sure FIBRIL is running and sending messages")
print("  ✓ Check firewall/network permissions")

print("\n  ISSUE: Receiving data but not parsing as OSC")
print("  ✓ Use [OSC-route] objects instead of [route]")
print("  ✓ OSC addresses start with / (e.g., /voice_1_MIDI)")
print("  ✓ Try [OpenSoundControl] library objects")

print("\n  ISSUE: Only some messages received")
print("  ✓ UDP buffer might be overflowing")
print("  ✓ Try increasing MaxMSP's UDP buffer size")
print("  ✓ We added 1ms delays to prevent flooding")

print("\n🔍 DEBUGGING STEPS:")
print("  1. Run FIBRIL and trigger a voice change")
print("  2. Look for '📤 SENDING N OSC MESSAGES' in terminal")
print("  3. In MaxMSP, temporarily connect [udpreceive 1762] to [print]")
print("  4. You should see binary data if UDP is working")
print("  5. If no data, check network/firewall")
print("  6. If seeing data, add OSC parsing")

print("\n📞 EXPECTED FIBRIL OUTPUT:")
print("  📤 SENDING 3 OSC MESSAGES TO MAXMSP (Port 1762):")
print("     /voice_1_* -> MIDI: 60, Volume: 1") 
print("     /voice_2_* -> Volume: 0")
print("     Total changed voices: 2")

print("\n✅ NEXT STEPS:")
print("  1. Start FIBRIL: python fibril_main.py")
print("  2. In MaxMSP: [udpreceive 1762] → [print]")
print("  3. Trigger voice changes in FIBRIL")
print("  4. If seeing data → add OSC parsing")
print("  5. If not seeing data → check network setup")

print("\n" + "=" * 40)
