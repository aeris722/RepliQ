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

class WhatsAppAIBot:
    def __init__(self):
        self.config_file = "bot_config.json"
        self.config = self.load_config()
        self.driver = None
        self.last_message = ""
        self.last_message_id = ""
        self.monitoring = False
        self.model = None
        
    def log(self, message):
        """Force print with flush"""
        print(message, flush=True)
        sys.stdout.flush()
        
    def load_config(self):
        """Load bot configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "api_key": "",
            "custom_prompt": "",
            "training_images": []
        }
    
    def save_config(self):
        """Save bot configuration"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def setup_gemini(self):
        """Initialize Google Gemini API"""
        self.log("\n" + "="*60)
        self.log("🔑 STEP 1: Setting up Google Gemini AI")
        self.log("="*60)
        
        if not self.config.get("api_key"):
            self.log("\n📋 First-time setup: Enter your Google Gemini API key")
            self.log("   Get it from: https://aistudio.google.com")
            self.log("   (Click 'Get API Key' → 'Create API Key')")
            api_key = input("\n   Paste your API key here: ").strip()
            
            if not api_key:
                self.log("❌ No API key provided. Exiting...")
                exit()
                
            self.config["api_key"] = api_key
            self.save_config()
            self.log("✅ API key saved!")
        else:
            self.log("✅ Using saved API key")
        
        try:
            genai.configure(api_key=self.config["api_key"])
            
            # Try multiple model names (API keeps changing)
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
                    self.log(f"   Trying model: {model_name}...")
                    test_model = genai.GenerativeModel(model_name)
                    test_response = test_model.generate_content("Say 'hi' in one word")
                    
                    # If we got here, it worked!
                    self.model = test_model
                    self.log(f"✅ Connected to {model_name}!")
                    self.log(f"✅ Test response: {test_response.text}")
                    break
                except Exception as e:
                    last_error = e
                    self.log(f"   ❌ {model_name} failed: {str(e)[:100]}")
                    continue
            
            if not self.model:
                # Try to list available models
                self.log("\n📋 Attempting to list available models...")
                try:
                    available_models = genai.list_models()
                    self.log("Available models:")
                    for m in available_models:
                        if 'generateContent' in m.supported_generation_methods:
                            self.log(f"   - {m.name}")
                            # Try the first available one
                            if not self.model:
                                try:
                                    model_name = m.name.replace('models/', '')
                                    self.model = genai.GenerativeModel(model_name)
                                    test = self.model.generate_content("hi")
                                    self.log(f"✅ Successfully using: {model_name}")
                                    break
                                except:
                                    continue
                except Exception as list_error:
                    self.log(f"   Could not list models: {list_error}")
                
                if not self.model:
                    raise last_error
            
        except Exception as e:
            self.log(f"❌ Failed to connect to Gemini: {e}")
            self.log(f"   Full error: {traceback.format_exc()}")
            self.log("\n   Possible issues:")
            self.log("   1. Check if your API key is correct")
            self.log("   2. Visit https://aistudio.google.com to verify your key")
            self.log("   3. Check if Gemini API is available in your region")
            self.config["api_key"] = ""
            self.save_config()
            exit()
    
    def setup_training_data(self):
        """Setup custom prompt and training images"""
        self.log("\n" + "="*60)
        self.log("🎨 STEP 2: Customize Your Bot's Texting Style")
        self.log("="*60)
        
        if not self.config.get("custom_prompt"):
            self.log("\n💬 Describe how YOU text:")
            prompt = input("\n   Your texting style: ").strip()
            
            if not prompt:
                prompt = "Casual and friendly, natural conversational tone"
                self.log(f"   Using default: {prompt}")
            
            self.config["custom_prompt"] = prompt
        else:
            self.log(f"✅ Using saved style: {self.config['custom_prompt'][:50]}...")
        
        if not self.config.get("training_images"):
            self.log("\n📸 Add chat screenshots? (yes/no): ")
            add_images = input().lower().strip()
            
            if add_images == 'yes':
                images = []
                self.log("\n   Select images (Cancel when done)")
                
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
                        self.log(f"   ✓ Added: {os.path.basename(file_path)}")
                    except:
                        break
                
                self.config["training_images"] = images
                if images:
                    self.log(f"\n✅ Added {len(images)} training images")
        else:
            self.log(f"✅ Using {len(self.config['training_images'])} saved images")
        
        self.save_config()
        self.log("✅ Bot customization complete!\n")
    
    def setup_whatsapp(self):
        """Initialize WhatsApp Web with Selenium"""
        self.log("="*60)
        self.log("🌐 STEP 3: Opening WhatsApp Web")
        self.log("="*60)
        
        try:
            self.log("\n🔧 Setting up Chrome browser...")
            
            options = Options()
            
            session_dir = os.path.abspath("./whatsapp_session")
            os.makedirs(session_dir, exist_ok=True)
            
            options.add_argument(f"--user-data-dir={session_dir}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.log("📦 Installing ChromeDriver...")
            
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.log("✅ Chrome opened!")
            self.log("\n🌐 Loading WhatsApp Web...")
            
            self.driver.get("https://web.whatsapp.com")
            
            self.log("\n" + "="*60)
            self.log("📱 SCAN QR CODE")
            self.log("="*60)
            self.log("\n   Waiting 120 seconds for scan...\n")
            
            try:
                WebDriverWait(self.driver, 120).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']"))
                )
                self.log("\n✅ WhatsApp connected!")
            except:
                self.log("\n   Trying alternative method...")
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox']"))
                )
                self.log("\n✅ WhatsApp connected!")
            
            time.sleep(3)
            
        except Exception as e:
            self.log(f"\n❌ Error: {str(e)}")
            traceback.print_exc()
            if self.driver:
                self.driver.quit()
            input("\nPress Enter to exit...")
            exit()
    
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
            self.log(f"   ⚠️ Image encoding error: {e}")
            return None
    
    def take_screenshot(self):
        """Take screenshot of WhatsApp for better context"""
        try:
            self.log("      [📸 Taking screenshot for context...]")
            screenshot = self.driver.get_screenshot_as_png()
            return screenshot
        except Exception as e:
            self.log(f"      [⚠️ Screenshot failed: {e}]")
            return None
    
    def get_conversation_context(self):
        """Get recent conversation messages for context"""
        try:
            self.log("      [📖 Reading conversation context...]")
            
            # Get all visible messages (both incoming and outgoing)
            all_messages = []
            
            # Get incoming messages
            incoming = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='message-in']")
            for msg in incoming[-5:]:  # Last 5 incoming
                try:
                    text = msg.find_element(By.CSS_SELECTOR, "span.selectable-text").text
                    if text.strip():
                        all_messages.append(f"Them: {text.strip()}")
                except:
                    pass
            
            # Get outgoing messages
            outgoing = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='message-out']")
            for msg in outgoing[-5:]:  # Last 5 outgoing
                try:
                    text = msg.find_element(By.CSS_SELECTOR, "span.selectable-text").text
                    if text.strip():
                        all_messages.append(f"You: {text.strip()}")
                except:
                    pass
            
            if all_messages:
                context = "\n".join(all_messages[-8:])  # Last 8 messages total
                self.log(f"      [✅ Got {len(all_messages[-8:])} messages of context]")
                return context
            
            return None
            
        except Exception as e:
            self.log(f"      [⚠️ Context reading failed: {e}]")
            return None
    
    def generate_reply(self, incoming_message):
        """Generate AI reply - ENHANCED WITH VISION AND CONTEXT"""
        try:
            self.log(f"      [Generating reply for: '{incoming_message[:50]}...']")
            
            # Get conversation context
            conversation_context = self.get_conversation_context()
            
            # Take screenshot for visual context
            screenshot = self.take_screenshot()
            
            # Build advanced prompt with context awareness
            system_prompt = f"""You are texting as this person. Analyze the message carefully and respond intelligently:

YOUR TEXTING STYLE:
{self.config['custom_prompt']}

RECENT CONVERSATION:
{conversation_context if conversation_context else "No previous context available"}

NEW MESSAGE TO REPLY TO:
"{incoming_message}"

CRITICAL INSTRUCTIONS:
1. ANALYZE the message first:
   - Is it a real message or gibberish (like "iuafgiudfirhuihccgh")?
   - What is the person actually asking or saying?
   - What's the appropriate response?

2. RESPOND INTELLIGENTLY:
   - If it's gibberish/random letters → ask "You okay?" or "Did you mean something?" or "???"
   - If it's a question → answer it properly
   - If it's a statement → engage with it meaningfully
   - If it's casual chat → match their energy
   - DO NOT just say "hn", "ok", "hmm" to everything

3. MATCH YOUR STYLE but be SMART:
   - Use the conversation history to stay relevant
   - Be contextually appropriate
   - Show you actually understood the message

4. FORMAT:
   - Write ONLY your reply (no labels, quotes, or explanations)
   - Keep it natural and conversational
   - 1-3 sentences usually

YOUR REPLY:"""
            
            # Build content with screenshot if available
            content_parts = [system_prompt]
            
            if screenshot:
                content_parts.append({
                    'mime_type': 'image/png',
                    'data': screenshot
                })
                self.log("      [🖼️ Including screenshot in AI analysis]")
            
            # Add training images if available
            if self.config.get("training_images"):
                self.log(f"      [📚 Using {len(self.config['training_images'])} training images]")
                for img_path in self.config["training_images"][:2]:
                    if os.path.exists(img_path):
                        img_data = self.encode_image(img_path)
                        if img_data:
                            content_parts.append({
                                'mime_type': 'image/jpeg',
                                'data': img_data
                            })
            
            # Generate config for intelligent responses
            generation_config = {
                'temperature': 1.1,  # Higher for more creative/varied responses
                'top_p': 0.95,
                'top_k': 50,
                'max_output_tokens': 200,
            }
            
            # Call the API
            self.log("      [🤖 Calling Gemini API with full context...]")
            
            response = self.model.generate_content(
                content_parts,
                generation_config=generation_config
            )
            
            if not response or not response.text:
                self.log("      [Empty response from API]")
                return "Hey! 👋"
            
            reply = response.text.strip()
            self.log(f"      [Raw API response: '{reply}']")
            
            # Clean up the response more aggressively
            # Remove quotes
            if reply.startswith('"') and reply.endswith('"'):
                reply = reply[1:-1].strip()
            if reply.startswith("'") and reply.endswith("'"):
                reply = reply[1:-1].strip()
            
            # Remove common prefixes
            prefixes = [
                "Reply:", "Response:", "Answer:", "Message:", "Your reply:",
                "reply:", "response:", "answer:", "message:", "your reply:"
            ]
            for prefix in prefixes:
                if reply.lower().startswith(prefix.lower()):
                    reply = reply[len(prefix):].strip()
            
            # Remove any leading/trailing special characters
            reply = reply.strip('*_~`')
            
            self.log(f"      [✅ Final reply: '{reply}']")
            
            # Validate reply
            if not reply or len(reply) < 1:
                self.log("      [Reply too short, using fallback]")
                return "Hey! 👋"
            
            return reply
            
        except Exception as e:
            self.log(f"   ❌ Error generating reply: {e}")
            self.log(f"   Full traceback: {traceback.format_exc()}")
            return "Hey! Let me get back to you 😊"
    
    def get_last_message(self):
        """Get last incoming message - IMPROVED"""
        try:
            time.sleep(1)
            
            # Find all message containers
            messages = self.driver.find_elements(By.CSS_SELECTOR, 
                "div[class*='message-in']")
            
            if not messages:
                # Alternative selector
                messages = self.driver.find_elements(By.XPATH,
                    "//div[contains(@class, 'message-in')]")
            
            if not messages:
                return None
            
            # Get the last incoming message
            last_msg = messages[-1]
            
            # Get message ID
            msg_id = last_msg.get_attribute('data-id')
            if not msg_id:
                # Fallback: use text hash as ID
                text_preview = last_msg.text[:30]
                msg_id = str(hash(text_preview + str(time.time())))
            
            # Extract text content
            text_elements = last_msg.find_elements(By.CSS_SELECTOR, 
                "span.selectable-text")
            
            if text_elements:
                text = " ".join([el.text.strip() for el in text_elements if el.text.strip()])
            else:
                text = last_msg.text.strip()
            
            # Clean up text
            lines = text.split('\n')
            clean_lines = [line.strip() for line in lines 
                          if line.strip() and not line.strip().isdigit() 
                          and len(line.strip()) > 2]
            
            text = ' '.join(clean_lines) if clean_lines else text
            
            if text and len(text) > 0:
                self.log(f"      ✅ Found message: {text[:60]}...")
                return {'text': text, 'id': msg_id}
            
            return None
            
        except Exception as e:
            self.log(f"      ❌ Error getting message: {e}")
            return None
    
    def send_message(self, message):
        """Send message - COMPLETELY REWRITTEN"""
        try:
            self.log(f"      [Sending: '{message[:50]}...']")
            time.sleep(1)
            
            # STEP 1: Find the input box
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
                        self.log(f"      [Found input box: {selector}]")
                        break
                except:
                    continue
            
            if not input_box:
                self.log("      ❌ Could not find input box")
                return False
            
            # STEP 2: Focus the input box
            self.log("      [Clicking input box...]")
            input_box.click()
            time.sleep(0.5)
            
            # STEP 3: Clear any existing text
            self.log("      [Clearing existing text...]")
            try:
                input_box.send_keys(Keys.CONTROL + 'a')
                time.sleep(0.1)
                input_box.send_keys(Keys.BACKSPACE)
                time.sleep(0.3)
            except:
                pass
            
            # STEP 4: Type the message using multiple methods
            success = False
            
            # Method 1: Direct send_keys
            try:
                self.log("      [Method 1: Direct typing...]")
                input_box.send_keys(message)
                time.sleep(0.5)
                
                # Verify text is there
                current_text = input_box.text or input_box.get_attribute('textContent') or ""
                if len(current_text) > 0:
                    self.log(f"      [Text entered: '{current_text[:30]}...']")
                    success = True
            except Exception as e:
                self.log(f"      [Method 1 failed: {e}]")
            
            # Method 2: JavaScript if Method 1 failed
            if not success:
                try:
                    self.log("      [Method 2: JavaScript injection...]")
                    self.driver.execute_script("""
                        var el = arguments[0];
                        var text = arguments[1];
                        
                        // Set text content
                        el.textContent = text;
                        el.innerText = text;
                        
                        // Trigger input events
                        var event = new InputEvent('input', {
                            bubbles: true,
                            cancelable: true,
                        });
                        el.dispatchEvent(event);
                        
                        // Force focus
                        el.focus();
                    """, input_box, message)
                    time.sleep(0.5)
                    
                    current_text = self.driver.execute_script(
                        "return arguments[0].textContent;", input_box)
                    
                    if len(current_text) > 0:
                        self.log(f"      [Text injected: '{current_text[:30]}...']")
                        success = True
                except Exception as e:
                    self.log(f"      [Method 2 failed: {e}]")
            
            if not success:
                self.log("      ❌ Failed to enter text")
                return False
            
            # STEP 5: Send the message
            self.log("      [Pressing Enter to send...]")
            time.sleep(0.3)
            
            try:
                # Try pressing Enter
                input_box.send_keys(Keys.RETURN)
                time.sleep(1)
                self.log("      ✅ Enter key pressed")
                
                # Verify message was sent (input should be empty now)
                time.sleep(1)
                final_text = input_box.text or input_box.get_attribute('textContent') or ""
                
                if len(final_text.strip()) == 0:
                    self.log("      ✅ Message sent successfully (input cleared)")
                    return True
                else:
                    self.log(f"      ⚠️ Input still has text: '{final_text[:30]}...'")
                    # Try clicking send button as backup
                    self.log("      [Trying send button...]")
                    try:
                        send_btn = self.driver.find_element(By.CSS_SELECTOR, 
                            "button[data-testid='send'], span[data-icon='send']")
                        send_btn.click()
                        time.sleep(1)
                        self.log("      ✅ Send button clicked")
                        return True
                    except:
                        self.log("      ⚠️ Send button not found")
                        return True  # Assume it worked if we got this far
                
            except Exception as e:
                self.log(f"      ❌ Error sending: {e}")
                return False
            
        except Exception as e:
            self.log(f"   ❌ Send error: {e}")
            self.log(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def show_approval_dialog(self, incoming_msg, suggested_reply):
        """Show approval dialog"""
        approved_reply = [None]
        
        def send_reply():
            approved_reply[0] = text_area.get("1.0", tk.END).strip()
            root.destroy()
        
        def cancel():
            root.destroy()
        
        root = tk.Tk()
        root.title("💬 Approve Reply")
        root.geometry("650x550")
        root.configure(bg='#075E54')
        root.attributes('-topmost', True)
        root.focus_force()
        
        # Header
        header = tk.Label(root, text="📨 New Message!", 
                         font=('Arial', 16, 'bold'), 
                         bg='#075E54', fg='white', pady=10)
        header.pack(fill='x')
        
        # Incoming
        tk.Label(root, text="From:", 
                font=('Arial', 10, 'bold'), 
                bg='#075E54', fg='#DCF8C6').pack(anchor='w', padx=20, pady=(10,5))
        
        incoming_frame = tk.Frame(root, bg='white', relief='solid', borderwidth=1)
        incoming_frame.pack(fill='x', padx=20, pady=5)
        
        incoming_text = tk.Label(incoming_frame, text=incoming_msg, 
                                font=('Arial', 11), 
                                bg='white', fg='black', 
                                wraplength=580, justify='left', pady=10, padx=10)
        incoming_text.pack(fill='x')
        
        # Reply
        tk.Label(root, text="Your Reply (edit if needed):", 
                font=('Arial', 10, 'bold'), 
                bg='#075E54', fg='#DCF8C6').pack(anchor='w', padx=20, pady=(15,5))
        
        text_area = scrolledtext.ScrolledText(root, height=10, 
                                             font=('Arial', 11), 
                                             wrap=tk.WORD, 
                                             bg='#DCF8C6', fg='black',
                                             borderwidth=2, relief='solid')
        text_area.pack(fill='both', expand=True, padx=20, pady=5)
        text_area.insert("1.0", suggested_reply)
        text_area.focus()
        
        # Buttons
        button_frame = tk.Frame(root, bg='#075E54')
        button_frame.pack(fill='x', pady=15)
        
        send_btn = tk.Button(button_frame, text="✅ Send", 
                           command=send_reply, 
                           font=('Arial', 12, 'bold'),
                           bg='#25D366', fg='white', 
                           padx=30, pady=10, cursor='hand2',
                           relief='raised', borderwidth=2)
        send_btn.pack(side='left', padx=(20,10))
        
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                              command=cancel, 
                              font=('Arial', 12, 'bold'),
                              bg='#D32F2F', fg='white', 
                              padx=30, pady=10, cursor='hand2',
                              relief='raised', borderwidth=2)
        cancel_btn.pack(side='left', padx=10)
        
        root.bind('<Control-Return>', lambda e: send_reply())
        
        root.mainloop()
        
        return approved_reply[0]
    
    def monitor_messages(self):
        """Main monitoring loop"""
        self.log("\n" + "="*60)
        self.log("👀 MONITORING STARTED")
        self.log("="*60)
        self.log("\n💡 Open a chat in WhatsApp Web")
        self.log("💡 Wait for incoming messages")
        self.log("💡 Keep this window open\n")
        self.log("-" * 60)
        
        self.monitoring = True
        check_count = 0
        message_count = 0
        
        while self.monitoring:
            try:
                check_count += 1
                
                if check_count % 5 == 0:
                    self.log(f"\n[{time.strftime('%H:%M:%S')}] Check #{check_count} - Active...")
                
                current_message_data = self.get_last_message()
                
                if current_message_data:
                    msg_text = current_message_data['text']
                    msg_id = current_message_data['id']
                    
                    # Check if this is a NEW message
                    if msg_id != self.last_message_id:
                        message_count += 1
                        self.last_message_id = msg_id
                        self.last_message = msg_text
                        
                        self.log(f"\n{'='*60}")
                        self.log(f"📨 NEW MESSAGE #{message_count}")
                        self.log(f"{'='*60}")
                        self.log(f"Text: {msg_text[:100]}")
                        self.log(f"ID: {msg_id}")
                        
                        self.log("\n🤖 Generating AI reply...")
                        suggested_reply = self.generate_reply(msg_text)
                        self.log(f"💡 AI Suggested: '{suggested_reply}'")
                        
                        self.log("\n⏸️ Showing approval dialog...")
                        approved = self.show_approval_dialog(msg_text, suggested_reply)
                        
                        if approved:
                            self.log(f"\n📤 User approved: '{approved}'")
                            self.log("      Sending message...")
                            
                            success = self.send_message(approved)
                            
                            if success:
                                self.log("✅ MESSAGE SENT SUCCESSFULLY!")
                            else:
                                self.log("❌ SEND FAILED - Please send manually")
                            
                            time.sleep(3)
                        else:
                            self.log("🚫 User cancelled")
                        
                        self.log("-" * 60)
                
                time.sleep(3)
                
            except KeyboardInterrupt:
                self.log("\n\n⏹️ Stopping...")
                self.monitoring = False
                break
            except Exception as e:
                self.log(f"\n⚠️ Error in loop: {e}")
                traceback.print_exc()
                time.sleep(5)
    
    def run(self):
        """Main execution"""
        self.log("\n" + "="*60)
        self.log("🤖 WHATSAPP AI BOT")
        self.log("="*60 + "\n")
        
        try:
            self.setup_gemini()
            self.setup_training_data()
            self.setup_whatsapp()
            self.monitor_messages()
            
        except KeyboardInterrupt:
            self.log("\n\n👋 Stopped by user")
        except Exception as e:
            self.log(f"\n❌ Fatal Error: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.log("\n🔄 Closing browser...")
                try:
                    self.driver.quit()
                except:
                    pass
            self.log("✅ Shutdown complete")
            input("\nPress Enter to exit...")

if __name__ == "__main__":
    bot = WhatsAppAIBot()
    bot.run()