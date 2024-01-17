from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium_stealth import stealth
# import undetected_chromedriver as uc
import time
import requests
import base64
from selenium.webdriver.common.action_chains import ActionChains
import math
import os


class TikTokBot:
    def __init__(self,username,password,callback=None):
        # self.username = "hoaly376977"
        # self.password = "@K4CzCOMxMN2R"
        self.username = username
        self.password = password
        self.callback = callback
        
        self.chrome_options = webdriver.ChromeOptions()
      
        self.driver = webdriver.Chrome(
            # os.path.join(path, 'chromedriver'),
            options=self.chrome_options)
        self.start_b = time.time()

        self.variables = [
            "https://www.tiktok.com/login/phone-or-email/email", "//input[@placeholder='Email or username']",
            "//input[@placeholder='Password']", "//button[@type='submit']"
        ]
        
    def get_chromedriver(self):
        chrome_options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(
            # os.path.join(path, 'chromedriver'),
            options=chrome_options)
        return driver
    def encode_response(self, response):
        if response.status_code == 200:
            encoded_data = base64.b64encode(response.content)
            return encoded_data.decode('utf-8')
        else:
            print(f"Failed to encode response. Status code: {response.status_code}")
            return None

    def send_api_request(self, encoded_inner_image, encoded_outer_image):
        api_url = "https://omocaptcha.com/api/createJob"
        api_key = "zRNjqIDpjur5aRONjGZts7wqewMzDmdZ3FUB5lPrTGIu6KNxJXSi6GrpgdIAMAyVIKn1HG81daaiEQUS"  
        payload = {
            "api_token": api_key,
            "data": {
                "type_job_id": "23",
                "image_base64": f"{encoded_inner_image}|{encoded_outer_image}"
            }
        }

        try:
            response = requests.post(api_url, json=payload)
            response.raise_for_status()
            print("API Request Successful")
            response_json = response.json()
            
            # job_id = response_json.get('job_id')
            # get_job_result(job_id)
            print("Response:", response.json())
        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
        return response_json

    def get_job_result(self, job_id):
        api_url = "https://omocaptcha.com/api/getJobResult"
        api_key = "zRNjqIDpjur5aRONjGZts7wqewMzDmdZ3FUB5lPrTGIu6KNxJXSi6GrpgdIAMAyVIKn1HG81daaiEQUS"
        
        
        max_retries = 4
        current_retry = 0

        while current_retry < max_retries:
            payload = {
                "api_token": api_key,
                "job_id": job_id
            }

            try:
                response = requests.post(api_url, json=payload)
                response.raise_for_status()

                result_json = response.json()
                print("Get Job Result Request Successful")
                print("Response:", result_json)

                
                status = result_json.get('status')
                if status == 'success':
                    return result_json  
                else:
                    print(f"Retry {current_retry + 1}/{max_retries}: Status is not success.")
                    current_retry += 1
                    time.sleep(5)  

            except requests.exceptions.HTTPError as errh:
                print(f"HTTP Error: {errh}")
                current_retry += 1
                time.sleep(5)  
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                current_retry += 1
                time.sleep(5)  

        print(f"Maximum number of retries reached. Could not get a successful response.")
        return result_json

    def resolve_recaptcha(self) -> bool:
        outer_img = "whirl-outer-img"
        outer_img_xpath = f'//*[@data-testid="{outer_img}"]'
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, outer_img_xpath)))

        outer_img_element = self.driver.find_element("xpath", outer_img_xpath)
        outer_image_url = outer_img_element.get_attribute('src')
       

        outer_image_response = requests.get(outer_image_url)
        encoded_outer_image = self.encode_response(outer_image_response)

        # whirl-inner-img
        inner_img = "whirl-inner-img"
        inner_img_xpath = f'//*[@data-testid="{inner_img}"]'
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, inner_img_xpath)))

        inner_img_element = self.driver.find_element("xpath", inner_img_xpath)
        inner_image_url = inner_img_element.get_attribute('src')
        

        inner_image_response = requests.get(inner_image_url)
        encoded_inner_image = self.encode_response(inner_image_response)

        button_xpath= '//*[@id="secsdk-captcha-drag-wrapper"]/div[2]'
        
        slide_xpath = '//*[@id="captcha_container"]/div/div[3]'

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, button_xpath)))
        button = self.driver.find_element(By.XPATH, button_xpath)
        slide =  self.driver.find_element(By.XPATH, slide_xpath)
        
        
        result_json = self.send_api_request(encoded_inner_image, encoded_outer_image)
        print(result_json)
        if result_json is not None:
                job_id = result_json.get('job_id')
                
                result = self.get_job_result(job_id)
                distance =result.get('result')
                distance = float(distance)
                if result is not None:
                        desired_offset =  distance 
                       

                # Use ActionChains to simulate dragging the button
                time.sleep(10)
                actions = ActionChains(self.driver)
                actions.click_and_hold(button).pause(0.2) 


                # Perform the drag and drop by moving the element pixel by pixel
                for _ in range(math.floor(int(desired_offset) / 5)):
                    actions.move_by_offset(5, 0) 

                for _ in range(int(desired_offset) % 5 - 1):
                    actions.move_by_offset(1, 0) 

                actions.release().perform()
                # actions.drag_and_drop_by_offset(button, desired_offset, 0)
                # actions.move_to_element(target_element).release().perform()
        
                # actions.perform() 
        return False
    
    
    
    def logging_in(self) -> bool:

        # if os.path.exists(self.user_profile_path):
        #     print("User profile exists. Skipping login.")
        #     return
        
        self.driver.get("https://www.tiktok.com/@proman.333/live")

        login_path = '//*[@id="loginContainer"]/div/div/div/div[2]/div'

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, login_path)))
        button = self.driver.find_element(By.XPATH, login_path)
        button.click()
        time.sleep(5)

        loginID_path = '//*[@id="loginContainer"]/div[2]/form/div[1]/a'

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, loginID_path)))
        button = self.driver.find_element(By.XPATH, loginID_path)
        button.click()
        time.sleep(5)

        variables = [
                    "https://www.tiktok.com/login/phone-or-email/email", "//input[@placeholder='Email or username']",
                    "//input[@placeholder='Password']", "//button[@type='submit']"
                ]
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, variables[1])))
            fieldForm = self.driver.find_element("xpath", variables[1])
        except:
            self.driver.quit()

        for i in self.username:
            fieldForm.send_keys(i)

        fieldForm = self.driver.find_element("xpath", variables[2])
        for i in self.password:
            fieldForm.send_keys(i)

        submit_path = '/html/body/div[17]/div[3]/div/div/div[1]/div[1]/div[2]/form/button'

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, submit_path)))
        button_submit = self.driver.find_element(By.XPATH, submit_path)
        button_submit.click()
        time.sleep(10)

        self.resolve_recaptcha()
        time.sleep(10)
        
        if self.callback:
                self.callback("Task completed successfully")
        return False

       


# if __name__ == "__main__":
#     tiktok_bot = TikTokBot()
#     tiktok_bot.logging_in()
#     end = time.time()
#     time.sleep(2)
    
# tiktok = TikTokBot()

