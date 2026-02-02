import os
import sys
import time
import json
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from PIL import Image
import io
import traceback
import random
import hashlib

# ANSI Color codes for terminal
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    WHITE = '\033[97m'
    BLACK = '\033[90m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

class LoadingAnimation:
    """Enhanced loading animations with matrix-style effects"""

    @staticmethod
    def show_boot_sequence():
        """Show RepliQ boot sequence with aesthetic animations"""
        messages = [
            "\n[*] Initializing RepliQ System...",
            "[*] Loading Advanced AI Modules...",
            "[*] Connecting to Gemini API...",
            "[*] Authenticating Credentials...",
            "[*] Scanning WhatsApp Web...",
        ]

        for msg in messages:
            print(f"{Colors.GREEN}{msg}{Colors.RESET}", flush=True)
            sys.stdout.flush()
            time.sleep(0.6)

            # Show matrix-style random code
            for _ in range(2):
                code_line = ''.join([random.choice('01#@$%&*') for _ in range(50)])
                print(f"{Colors.BLACK}{code_line}{Colors.RESET}", flush=True)
                sys.stdout.flush()
                time.sleep(0.2)

    @staticmethod
    def show_loading_bar(duration=3):
        """Show animated loading bar with internet speed"""
        print(f"\n{Colors.CYAN}[CONNECTING TO MODULES]{Colors.RESET}")

        total_steps = 30
        for i in range(total_steps + 1):
            percent = (i / total_steps) * 100
            filled = int(i / total_steps * 20)

            # Simulate internet speed
            speed = random.randint(1, 100)

            bar = f"{Colors.GREEN}{'█' * filled}{Colors.WHITE}{'░' * (20 - filled)}{Colors.RESET}"
            print(f"  {bar} {percent:.0f}% | {Colors.YELLOW}{speed} Mbps{Colors.RESET}", end="\r", flush=True)
            sys.stdout.flush()
            time.sleep(duration / total_steps)

        print(f"  {Colors.GREEN}{'█' * 20}{Colors.RESET} 100% | {Colors.YELLOW}95 Mbps{Colors.RESET} ✓\n")
        sys.stdout.flush()

    @staticmethod
    def show_authenticator():
        """Show authenticator animation"""
        print(f"{Colors.CYAN}[AUTHENTICATOR SEQUENCE]{Colors.RESET}")

        auth_steps = [
            "Verifying API Keys...",
            "Checking Browser Automation...",
            "Validating WhatsApp Session...",
            "Initializing Message Monitor...",
            "System Ready!",
        ]

        for step in auth_steps:
            status = f"{Colors.GREEN}✓{Colors.RESET}" if step != "System Ready!" else f"{Colors.GREEN}✓✓{Colors.RESET}"
            print(f"  {status} {step}")
            sys.stdout.flush()
            time.sleep(0.5)

class WhatsAppAIBot:
    def __init__(self):
        self.config_file = "bot_config.json"
        self.config = self.load_config()
        self.driver = None
        self.last_message = ""
        self.last_message_hash = ""  # Changed from ID to hash for better duplicate detection
        self.message_history = set()  # Store hashes of all replied messages
        self.monitoring = False
        self.model = None

    def log(self, message, color=Colors.WHITE):
        """Enhanced logging with colors"""
        print(f"{color}{message}{Colors.RESET}", flush=True)
        sys.stdout.flush()

    def load_config(self):
        """Load bot configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "api_key": "",
            "custom_prompt": "",
            "training_images": [],
            "replied_messages": []  # New field to store replied message hashes
        }

    def save_config(self):
        """Save bot configuration"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def setup_gemini(self):
        """Initialize Google Gemini API with enhanced visuals"""
        self.log("\n" + "="*60, Colors.CYAN)
        self.log("🔑 STEP 1: Setting up Google Gemini AI", Colors.GREEN)
        self.log("="*60, Colors.CYAN)

        if not self.config.get("api_key"):
            self.log("\n📋 First-time setup: Enter your Google Gemini API key", Colors.YELLOW)
            self.log(" Get it from: https://aistudio.google.com", Colors.WHITE)
            self.log(" (Click 'Get API Key' → 'Create API Key')", Colors.WHITE)
            api_key = input(f"\n{Colors.GREEN} Paste your API key here: {Colors.RESET}").strip()
            if not api_key:
                self.log("❌ No API key provided. Exiting...", Colors.RED)
                exit()
            self.config["api_key"] = api_key
            self.save_config()
            self.log("✅ API key saved!", Colors.GREEN)
        else:
            self.log("✅ Using saved API key", Colors.GREEN)

        try:
            genai.configure(api_key=self.config["api_key"])
            models_to_try = [
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash',
                'gemini-pro',
                'gemini-1.5-pro-latest'
            ]

            self.model = None
            last_error = None
            for model_name in models_to_try:
                try:
                    self.log(f" Trying model: {model_name}...", Colors.WHITE)
                    test_model = genai.GenerativeModel(model_name)
                    test_response = test_model.generate_content("Say 'hi' in one word")
                    self.model = test_model
                    self.log(f"✅ Connected to {model_name}!", Colors.GREEN)
                    break
                except Exception as e:
                    last_error = e
                    self.log(f" ❌ {model_name} failed", Colors.RED)
                    continue

            if not self.model:
                raise last_error

            LoadingAnimation.show_loading_bar()
            LoadingAnimation.show_authenticator()

        except Exception as e:
            self.log(f"❌ Failed to connect to Gemini: {e}", Colors.RED)
            self.config["api_key"] = ""
            self.save_config()
            exit()

    def setup_training_data(self):
        """Setup custom prompt and training images"""
        self.log("\n" + "="*60, Colors.CYAN)
        self.log("🎨 STEP 2: Customize Your Bot's Texting Style", Colors.GREEN)
        self.log("="*60, Colors.CYAN)

        if not self.config.get("custom_prompt"):
            self.log("\n💬 Describe how YOU text:", Colors.YELLOW)
            prompt = input(f"{Colors.GREEN} Your texting style: {Colors.RESET}").strip()
            if not prompt:
                prompt = "Casual and friendly, natural conversational tone"
                self.log(f" Using default: {prompt}", Colors.WHITE)
            self.config["custom_prompt"] = prompt
        else:
            self.log(f"✅ Using saved style: {self.config['custom_prompt'][:50]}...", Colors.GREEN)

        if not self.config.get("training_images"):
            self.log("\n📸 Add chat screenshots? (yes/no): ", Colors.YELLOW)
            add_images = input().lower().strip()
            if add_images == 'yes':
                images = []
                self.log("\n Select images (Cancel when done)", Colors.WHITE)
                while True:
                    try:
                        root = tk.Tk()
                        root.withdraw()
                        root.attributes('-topmost', True)
                        file_path = filedialog.askopenfilename(
                            title="Select chat screenshot",
                            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
                        )
                        root.destroy()
                        if not file_path:
                            break
                        images.append(file_path)
                        self.log(f" ✓ Added: {os.path.basename(file_path)}", Colors.GREEN)
                    except:
                        break
                self.config["training_images"] = images

        self.save_config()
        self.log("✅ Bot customization complete!\n", Colors.GREEN)

    def setup_whatsapp(self):
        """Initialize WhatsApp Web with Selenium"""
        self.log("="*60, Colors.CYAN)
        self.log("🌐 STEP 3: Opening WhatsApp Web", Colors.GREEN)
        self.log("="*60, Colors.CYAN)

        try:
            self.log("\n🔧 Setting up Chrome browser...", Colors.WHITE)
            options = Options()
            session_dir = os.path.abspath("./whatsapp_session")
            os.makedirs(session_dir, exist_ok=True)
            options.add_argument(f"--user-data-dir={session_dir}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            self.log("📦 Installing ChromeDriver...", Colors.WHITE)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.log("✅ Chrome opened!", Colors.GREEN)

            self.log("\n🌐 Loading WhatsApp Web...", Colors.WHITE)
            self.driver.get("https://web.whatsapp.com")

            self.log("\n" + "="*60, Colors.CYAN)
            self.log("📱 SCAN QR CODE", Colors.YELLOW)
            self.log("="*60, Colors.CYAN)
            self.log("\n Waiting 120 seconds for scan...\n", Colors.WHITE)

            try:
                WebDriverWait(self.driver, 120).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']"))
                )
                self.log("\n✅ WhatsApp connected!", Colors.GREEN)
            except:
                self.log("\n Trying alternative method...", Colors.YELLOW)
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox']"))
                )
                self.log("\n✅ WhatsApp connected!", Colors.GREEN)
            time.sleep(3)

        except Exception as e:
            self.log(f"\n❌ Error: {str(e)}", Colors.RED)
            if self.driver:
                self.driver.quit()
            input("\nPress Enter to exit...")
            exit()

    def get_message_hash(self, message_text):
        """Generate hash of message to detect duplicates"""
        return hashlib.sha256(message_text.encode()).hexdigest()

    def encode_image(self, image_path):
        """Encode image for Gemini"""
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                max_size = (1024, 1024)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                return buffer.getvalue()
        except Exception as e:
            self.log(f" ⚠️ Image encoding error: {e}", Colors.YELLOW)
            return None

    def take_screenshot(self):
        """Take screenshot of WhatsApp for better context"""
        try:
            self.log(" [📸 Taking full screenshot for context...]", Colors.CYAN)
            screenshot = self.driver.get_screenshot_as_png()
            return screenshot
        except Exception as e:
            self.log(f" [⚠️ Screenshot failed: {e}]", Colors.YELLOW)
            return None

    def get_conversation_context(self):
        """Get recent conversation messages for context"""
        try:
            self.log(" [📖 Reading full conversation context...]", Colors.CYAN)
            all_messages = []

            incoming = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='message-in']")
            for msg in incoming[-10:]:
                try:
                    text = msg.find_element(By.CSS_SELECTOR, "span.selectable-text").text
                    if text.strip():
                        all_messages.append(f"Them: {text.strip()}")
                except:
                    pass

            outgoing = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='message-out']")
            for msg in outgoing[-10:]:
                try:
                    text = msg.find_element(By.CSS_SELECTOR, "span.selectable-text").text
                    if text.strip():
                        all_messages.append(f"You: {text.strip()}")
                except:
                    pass

            if all_messages:
                context = "\n".join(all_messages[-15:])
                self.log(f" [✅ Got full conversation context]", Colors.GREEN)
                return context
            return None

        except Exception as e:
            self.log(f" [⚠️ Context reading failed: {e}]", Colors.YELLOW)
            return None

    def generate_reply(self, incoming_message):
        """Generate AI reply with full screenshot and context"""
        try:
            self.log(f" [Generating intelligent reply...]", Colors.CYAN)

            conversation_context = self.get_conversation_context()
            screenshot = self.take_screenshot()

            system_prompt = f"""You are texting as this person. Analyze the message and respond naturally.

YOUR TEXTING STYLE:
{self.config['custom_prompt']}

RECENT CONVERSATION:
{conversation_context if conversation_context else "No previous messages"}

NEW MESSAGE TO REPLY TO:
"{incoming_message}"

INSTRUCTIONS:
1. Analyze the message carefully - Is it a real message or gibberish?
2. If gibberish (random letters) → ask "You okay?" or "Did you mean something?" or "???"
3. If real → respond naturally and match the conversation
4. Show you understood the message
5. Keep it 1-3 sentences, natural and conversational
6. Write ONLY your reply, no explanations

YOUR REPLY:"""

            content_parts = [system_prompt]

            if screenshot:
                content_parts.append({
                    'mime_type': 'image/png',
                    'data': screenshot
                })
                self.log(" [🖼️ Full screenshot included for context]", Colors.GREEN)

            if self.config.get("training_images"):
                self.log(f" [📚 Using {len(self.config['training_images'])} training images]", Colors.YELLOW)
                for img_path in self.config["training_images"][:2]:
                    if os.path.exists(img_path):
                        img_data = self.encode_image(img_path)
                        if img_data:
                            content_parts.append({
                                'mime_type': 'image/jpeg',
                                'data': img_data
                            })

            generation_config = {
                'temperature': 1.1,
                'top_p': 0.95,
                'top_k': 50,
                'max_output_tokens': 200,
            }

            self.log(" [🤖 Calling Gemini AI...]", Colors.CYAN)
            response = self.model.generate_content(
                content_parts,
                generation_config=generation_config
            )

            if not response or not response.text:
                self.log(" [Empty response from API]", Colors.YELLOW)
                return "Hey! 👋"

            reply = response.text.strip()
            self.log(f" [Raw response: '{reply[:50]}...']", Colors.WHITE)

            if reply.startswith('\"') and reply.endswith('\"'):
                reply = reply[1:-1].strip()
            if reply.startswith("'") and reply.endswith("'"):
                reply = reply[1:-1].strip()

            prefixes = [
                "Reply:", "Response:", "Answer:", "Message:", "Your reply:",
                "reply:", "response:", "answer:", "message:", "your reply:"
            ]
            for prefix in prefixes:
                if reply.lower().startswith(prefix.lower()):
                    reply = reply[len(prefix):].strip()

            reply = reply.strip('*_~`')

            if not reply or len(reply) < 1:
                self.log(" [Reply too short, using fallback]", Colors.YELLOW)
                return "Hey! 👋"

            self.log(f" [✅ Final reply: '{reply}']", Colors.GREEN)
            return reply

        except Exception as e:
            self.log(f" ❌ Error generating reply: {e}", Colors.RED)
            return "Hey! Let me get back to you 😊"

    def get_last_message(self):
        """Get last incoming message with improved detection"""
        try:
            time.sleep(1)
            messages = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='message-in']")

            if not messages:
                messages = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]")

            if not messages:
                return None

            last_msg = messages[-1]

            text_elements = last_msg.find_elements(By.CSS_SELECTOR, "span.selectable-text")
            if text_elements:
                text = " ".join([el.text.strip() for el in text_elements if el.text.strip()])
            else:
                text = last_msg.text.strip()

            lines = text.split('\n')
            clean_lines = [line.strip() for line in lines
                          if line.strip() and not line.strip().isdigit()
                          and len(line.strip()) > 2]
            text = ' '.join(clean_lines) if clean_lines else text

            if text and len(text) > 0:
                msg_hash = self.get_message_hash(text)
                self.log(f" ✅ Found message: {text[:60]}...", Colors.GREEN)
                return {'text': text, 'hash': msg_hash}

            return None

        except Exception as e:
            self.log(f" ❌ Error getting message: {e}", Colors.RED)
            return None

    def send_message(self, message):
        """Send message with multiple fallback methods"""
        try:
            self.log(f" [Sending: '{message[:50]}...']", Colors.CYAN)
            time.sleep(1)

            input_box = None
            selectors = [
                "div[contenteditable='true'][data-tab='10']",
                "div[contenteditable='true'][role='textbox']",
                "footer div[contenteditable='true']",
            ]

            for selector in selectors:
                try:
                    input_box = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if input_box.is_displayed():
                        self.log(f" [Found input box]", Colors.GREEN)
                        break
                except:
                    continue

            if not input_box:
                self.log(" ❌ Could not find input box", Colors.RED)
                return False

            self.log(" [Clicking input box...]", Colors.WHITE)
            input_box.click()
            time.sleep(0.5)

            self.log(" [Clearing existing text...]", Colors.WHITE)
            try:
                input_box.send_keys(Keys.CONTROL + 'a')
                time.sleep(0.1)
                input_box.send_keys(Keys.BACKSPACE)
                time.sleep(0.3)
            except:
                pass

            success = False

            try:
                self.log(" [Method 1: Direct typing...]", Colors.WHITE)
                input_box.send_keys(message)
                time.sleep(0.5)
                current_text = input_box.text or input_box.get_attribute('textContent') or ""
                if len(current_text) > 0:
                    self.log(f" [Text entered]", Colors.GREEN)
                    success = True
            except Exception as e:
                self.log(f" [Method 1 failed]", Colors.YELLOW)

            if not success:
                try:
                    self.log(" [Method 2: JavaScript injection...]", Colors.WHITE)
                    self.driver.execute_script("""
                    var el = arguments[0];
                    var text = arguments[1];
                    el.textContent = text;
                    el.innerText = text;
                    var event = new InputEvent('input', {bubbles: true, cancelable: true});
                    el.dispatchEvent(event);
                    el.focus();
                    """, input_box, message)
                    time.sleep(0.5)
                    success = True
                except Exception as e:
                    self.log(f" [Method 2 failed]", Colors.YELLOW)

            if not success:
                self.log(" ❌ Failed to enter text", Colors.RED)
                return False

            self.log(" [Pressing Enter to send...]", Colors.WHITE)
            time.sleep(0.3)
            input_box.send_keys(Keys.RETURN)
            time.sleep(1)

            self.log(" ✅ Message sent successfully", Colors.GREEN)
            return True

        except Exception as e:
            self.log(f" ❌ Send error: {e}", Colors.RED)
            return False

    def show_approval_dialog(self, incoming_msg, suggested_reply):
        """Show dark mode approval dialog with RepliQ logo"""
        approved_reply = [None]

        def send_reply():
            approved_reply[0] = text_area.get("1.0", tk.END).strip()
            root.destroy()

        def cancel():
            root.destroy()

        root = tk.Tk()
        root.title("RepliQ - Reply Approval")
        root.geometry("700x600")
        root.configure(bg='#1a1a1a')
        root.attributes('-topmost', True)
        root.focus_force()

        # Dark mode header with logo
        header_frame = tk.Frame(root, bg='#2d2d2d', height=70)
        header_frame.pack(fill='x')

        logo_label = tk.Label(header_frame, text="⚡ RepliQ", 
                            font=('Arial', 20, 'bold'),
                            bg='#2d2d2d', fg='#00FF00', pady=10)
        logo_label.pack(side='left', padx=20)

        status_label = tk.Label(header_frame, text="● Active", 
                              font=('Arial', 10),
                              bg='#2d2d2d', fg='#00FF00')
        status_label.pack(side='right', padx=20, pady=15)

        # Incoming message section
        incoming_label = tk.Label(root, text="📨 New Message Detected:",
                                font=('Arial', 11, 'bold'),
                                bg='#1a1a1a', fg='#FF5555', pady=10)
        incoming_label.pack(anchor='w', padx=20)

        incoming_frame = tk.Frame(root, bg='#2d2d2d', relief='solid', borderwidth=2)
        incoming_frame.pack(fill='x', padx=20, pady=5)

        incoming_text = tk.Label(incoming_frame, text=incoming_msg,
                               font=('Arial', 11),
                               bg='#2d2d2d', fg='#FFFFFF',
                               wraplength=630, justify='left', pady=12, padx=12)
        incoming_text.pack(fill='x')

        # Reply section
        reply_label = tk.Label(root, text="💬 Suggested Reply (edit if needed):",
                             font=('Arial', 11, 'bold'),
                             bg='#1a1a1a', fg='#00FF00', pady=10)
        reply_label.pack(anchor='w', padx=20)

        text_area = scrolledtext.ScrolledText(root, height=10,
                                            font=('Courier', 10),
                                            wrap=tk.WORD,
                                            bg='#2d2d2d', fg='#00FF00',
                                            insertbackground='#FF5555',
                                            borderwidth=2, relief='solid')
        text_area.pack(fill='both', expand=True, padx=20, pady=5)
        text_area.insert("1.0", suggested_reply)
        text_area.focus()

        # Button frame
        button_frame = tk.Frame(root, bg='#1a1a1a')
        button_frame.pack(fill='x', pady=15)

        send_btn = tk.Button(button_frame, text="✅ SEND",
                           command=send_reply,
                           font=('Arial', 12, 'bold'),
                           bg='#00AA00', fg='#000000',
                           padx=35, pady=10, cursor='hand2',
                           relief='raised', borderwidth=2, 
                           activebackground='#00FF00')
        send_btn.pack(side='left', padx=(20,10))

        cancel_btn = tk.Button(button_frame, text="❌ CANCEL",
                             command=cancel,
                             font=('Arial', 12, 'bold'),
                             bg='#FF5555', fg='#FFFFFF',
                             padx=30, pady=10, cursor='hand2',
                             relief='raised', borderwidth=2,
                             activebackground='#FF8888')
        cancel_btn.pack(side='left', padx=10)

        root.bind('<Return>', lambda e: send_reply())
        root.mainloop()

        return approved_reply[0]

    def monitor_messages(self):
        """Main monitoring loop with duplicate detection"""
        self.log("\n" + "="*60, Colors.CYAN)
        self.log("👀 MONITORING STARTED - RepliQ Active", Colors.GREEN)
        self.log("="*60, Colors.CYAN)
        self.log("\n💡 Open a chat in WhatsApp Web", Colors.WHITE)
        self.log("💡 Wait for incoming messages", Colors.WHITE)
        self.log("💡 Keep this window open\n", Colors.WHITE)
        self.log("-" * 60, Colors.BLACK)

        self.monitoring = True
        check_count = 0
        message_count = 0

        # Load previously replied messages
        self.message_history = set(self.config.get("replied_messages", []))

        while self.monitoring:
            try:
                check_count += 1
                if check_count % 5 == 0:
                    self.log(f"\n[{time.strftime('%H:%M:%S')}] Check #{check_count} - Active...", Colors.WHITE)

                current_message_data = self.get_last_message()

                if current_message_data:
                    msg_text = current_message_data['text']
                    msg_hash = current_message_data['hash']

                    # ✅ CRITICAL: Check if we already replied to this message
                    if msg_hash not in self.message_history:
                        message_count += 1
                        self.message_history.add(msg_hash)
                        self.last_message_hash = msg_hash

                        # Save to config so it persists
                        self.config["replied_messages"] = list(self.message_history)
                        self.save_config()

                        self.log(f"\n{'='*60}", Colors.CYAN)
                        self.log(f"📨 NEW MESSAGE #{message_count}", Colors.GREEN)
                        self.log(f"{'='*60}", Colors.CYAN)
                        self.log(f"Text: {msg_text[:100]}", Colors.WHITE)
                        self.log(f"Hash: {msg_hash[:16]}...", Colors.YELLOW)

                        self.log("\n🤖 Generating AI reply...", Colors.CYAN)
                        suggested_reply = self.generate_reply(msg_text)
                        self.log(f"💡 AI Suggested: '{suggested_reply}'", Colors.GREEN)

                        self.log("\n⏸️ Showing approval dialog...", Colors.YELLOW)
                        approved = self.show_approval_dialog(msg_text, suggested_reply)

                        if approved:
                            self.log(f"\n📤 User approved: '{approved}'", Colors.GREEN)
                            self.log(" Sending message...", Colors.WHITE)
                            success = self.send_message(approved)
                            if success:
                                self.log("✅ MESSAGE SENT SUCCESSFULLY!", Colors.GREEN)
                            else:
                                self.log("❌ SEND FAILED - Please send manually", Colors.RED)
                            time.sleep(3)
                        else:
                            self.log("🚫 User cancelled", Colors.YELLOW)

                        self.log("-" * 60, Colors.BLACK)
                    else:
                        # Message already replied to
                        if check_count % 10 == 0:
                            self.log(f"[{time.strftime('%H:%M:%S')}] Already replied to this message, waiting for new ones...", Colors.BLACK)

                time.sleep(3)

            except KeyboardInterrupt:
                self.log("\n\n⏹️ Stopping RepliQ...", Colors.RED)
                self.monitoring = False
                break

            except Exception as e:
                self.log(f"\n⚠️ Error in loop: {e}", Colors.RED)
                traceback.print_exc()
                time.sleep(5)

    def run(self):
        """Main execution with boot sequence"""
        LoadingAnimation.show_boot_sequence()

        self.log("\n" + "="*60, Colors.CYAN)
        self.log("🤖 REPLIQI - AI WHATSAPP BOT", Colors.GREEN)
        self.log("="*60 + "\n", Colors.CYAN)

        try:
            self.setup_gemini()
            self.setup_training_data()
            self.setup_whatsapp()
            self.monitor_messages()

        except KeyboardInterrupt:
            self.log("\n\n👋 Stopped by user", Colors.YELLOW)

        except Exception as e:
            self.log(f"\n❌ Fatal Error: {e}", Colors.RED)
            traceback.print_exc()

        finally:
            if self.driver:
                self.log("\n🔄 Closing browser...", Colors.YELLOW)
                try:
                    self.driver.quit()
                except:
                    pass
            self.log("✅ Shutdown complete", Colors.GREEN)
            input("\nPress Enter to exit...")

if __name__ == "__main__":
    bot = WhatsAppAIBot()
    bot.run()
