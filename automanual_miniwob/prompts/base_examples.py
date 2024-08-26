
enter_example = '''
Your task is to Enter "Ronda" into the text field and press Submit.
...(HTML)...

### Understanding of the observation: ...
### Plan for the task: I should click the input box, then type "Ronda" and click the submit button.
### Code
```python
# [Step 1] Click the input box
inputbox_xpath = "//input[@id='tt']"
agent.click_xpath(inputbox_xpath)

# [Step 2] Type "Ronda" into the input box
agent.type("Ronda")

# [Step 3] Click the submit button
submit_button_xpath = "//button[@id='subbtn']"
agent.click_xpath(submit_button_xpath)
```
'''

search_example = '''
Your task is to Use the textbox to enter "Jerald" and press "Search", then find and click the 4th search result.
...(HTML)...

### Understanding of the observation: ...
### Plan for the task: First, I need to click <input> textbox and type "Jerald". Then click "Search" button and check the result. After that I need to navigate to and click on the 4th search result.
### Code
```python
# [Step 1] Find <input> textbox and type "Jerald".
textbox_xpath = "//*[@id='search-text']"
agent.click_xpath(textbox_xpath)
agent.type("Jerald")

# [Step 2] Click the search button
search_button_xpath = "//*[@id='search']"
html_string = agent.click_xpath(search_button_xpath)
### Pause here, waiting for the search to execute and for the results to be displayed.

# [Step 3] Turn to the next page for the 4th search result, since one page only display 3 search results
next_page_xpath = f"//*[@id='pagination']/li[@class='page-item next']"
html_string = agent.click_xpath(next_page_xpath)
# click the 4th search result
result_xpath = f"//*[@id='page-content']//a[@data-result='3']" # data-result start from 0
agent.click_xpath(result_xpath)
```
'''.strip()


example_list = {
    'click-menu':
'''
Task: Select Alice > Bob > Carol
### General plan: I should move mouse to Alice to make the submenu show up, then I should move mouse to Bob make the submenu show up, finally I should click Carol.
```python
# [Step 1] move mouse to Alice
agent.move_mouse_on("//div[contains(text(), 'Alice')]")

# [Step 2] move mouse to Bob
agent.move_mouse_on("//div[contains(text(), 'Bob')]")

# [Step 3] click Carol
agent.click_xpath("//div[contains(text(), 'Carol')]")
```
'''.strip(),
    'enter-date': 
'''
Task: Enter 08/20/2022 as the date and hit submit.
### General plan: I should click the input box, then press the left_arrow twice to move the cursor to the beginning of the input box, finally type 08/20/2022 and click the submit button.
```python
# [Step 1] click the input box of date
agent.click_xpath("//input[@id='tt']")

# [Step 2] press the left_arrow twice to move the cursor to the beginning of the input box
agent.press("arrow_left")
agent.press("arrow_left")

# [Step 3] type 08/20/2022 in the input box
agent.type("08/20/2022")

# [Step 4] click the submit
agent.click_xpath("//*[@id='subbtn']")
```
'''.strip(),
    'enter-time': 
'''
Task: Enter 5:20 PM as the time and press submit.
### General plan: I should click the input box, then type the time and click the submit button.
```python
# [Step 1] click the input box of date
agent.click_xpath("//*[@id='tt']")

# [Step 2] format the time
# I must type 0520PM because the ':' and space will be automatically added by the webpage. Note that a zero is added before 5 to satisfy the format HHMMAM or HHMMPM.
formatted_time = "0520PM"

# [Step 3] type the time in the input box
agent.type(formatted_time)

# [Step 4] click the submit
agent.click_xpath("//*[@id='subbtn']")
```
'''.strip(),
    'social-media-some':
'''
# Here are two examples of solution.
# Task: Click the "Reply" button on 2 posts by @sergio and then click Submit.
### General plan: I should first click the "Reply" button for 2 posts by @sergio, and then click the Submit button.
```python
# [Step 1] Click the "Reply" button for 2 posts by @sergio
# I can click the first unselected "Reply" button twice in a loop
for i in range(2):
    agent.click_xpath(f"//div[@class='media'][.//span[@class='username' and text()='@sergio']][{i+1}]//span[@class='reply']")

# [Step 2] Click the Submit button
agent.click_xpath("//button[@type='button']")

# Task: Click the "Like" button on 1 post by @alice and then click Submit.
### General plan: I should first click the "Like" button for only 1 post by @alice, and then click the Submit button.
```python
# [Step 1] Click the "Like" button for 1 post by @alice
# I only need to click the first "Like" button once
xpath_of_like_button = "//div[@class='media'][.//span[@class='username' and text()='@alice']][1]//span[@class='like']")
agent.click_xpath(xpath_of_like_button)

# [Step 2] Click the Submit button
agent.click_xpath("//button[@type='button']")
```
'''.strip()
}