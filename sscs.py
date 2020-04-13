from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import time

def init():
    # the firefox binary must also be included in the PATH
    #driver = webdriver.Firefox(executable_path='\path\to\geckodriver.exe')
    # if the geckodriver binary is included in the PATH, there is no need to explicitly pass executable_path
    driver = webdriver.Firefox()

    driver.get("https://resourcecenter.sscs.ieee.org")

    return driver

# Automatically adds school address
def addaddress(driver):
    # go to address information page
    print("Adding primary address...")
    driver.get("https://www.ieee.org/profile/address/getAddrInfoPage.html")

    # runs JavaScript that shows the form for adding a new address
    time.sleep(1)
    driver.execute_script("javascript:ManageAddress.showdatafromurl('/profile/address/getAddressDetails.html','','add-new-address');plusToMinunsImg(this);")

    # fills up the form
    time.sleep(3)
    driver.find_element_by_id("addressType-3").click()
    driver.find_element_by_id("address-line1").send_keys("EEEI Bldg, Velasquez St, UP Diliman")
    driver.find_element_by_id("city").send_keys("Quezon City")
    driver.find_element_by_id("postal-code").send_keys("1101")
    driver.find_element_by_id("primAddFlag").click()
    driver.find_element_by_id("saveAddrButtonId").click()
    time.sleep(5)

# Extract all links
def extractlinks(driver, jsonfile='links.json'):
    a_tags = driver.find_elements_by_css_selector("article.content a")
    duplicate_href = []

    for a in a_tags:
        duplicate_href.append(a.get_attribute("href"))

    unique_links = list(set(duplicate_href))
    with open(jsonfile, 'w') as f:
        json.dump(unique_links, f)

# Extract links from links.json
def parselinks(jsonfile='links.json'):
    print("Parsing list of links from %s..." % (jsonfile))
    with open(jsonfile) as f:
        links = json.load(f)

    return links

# Add resources to cart based on given links
def autoaddtocart(driver, links, maxcart=100):
    # go to link that has an onclick event
    # hardcoded link since this resource is not free and not purchased therefore an add to cart event exists
    driver.get("https://resourcecenter.sscs.ieee.org/publications/ebooks/SSCSeBook001.html")

    # get initial cart count
    # large delay needed if many items are in the cart
    print("Getting initial cart count...")
    time.sleep(20)
    cart = int(driver.find_element_by_id("mn-cart-item-qty").text)
    
    if (cart >= maxcart):
        # checkout if cart is full based on maxcart
        print("Cart is full. Checking total amount...")
        abort = checkout(driver)

    # close cookie message
    try:
        driver.find_element_by_css_selector("a.cc-btn.cc-dismiss").click()
    except:
        pass

    l = 0
    cart = 0

    print("Proceeding to add resources to cart...")
    for link in links:
        l = l + 1

        if (cart < maxcart):
            print("(Link %d/%d) Checking link %s..." % (l, len(links), link))

            # parse last part of link to get onclick event
            rs = link.rsplit('/')[-1][:-5]

            time.sleep(2)
            try:
                driver.execute_script("rcCart.checkoutClickEvent('%s');" % (rs))
                cart = cart + 1
                print("%s added to cart. Add to cart attempts left: %d" % (rs, maxcart - cart))
            except:
                print("\tResource already purchased/added to cart before\n")
        else:
            # check actual cart counter
            # delay needed so that previous add to cart events are resolved properly
            time.sleep(3)
            driver.get(link)
            time.sleep(10)
            prev_cart = cart
            cart = int(driver.find_element_by_id("mn-cart-item-qty").text)
            
            if not (prev_cart == cart):
                print("Cart counter: %d\nActual cart contents: %d" % (prev_cart, cart))

            if (cart >= maxcart):
                # checkout if cart is full based on maxcart
                print("Cart is full. Checking total amount...")
                abort = checkout(driver)

    if not (len(links) == 0):
        checkout(driver)
    else:
        print("Nothing to add to cart.")

# checks purchased resources and removes them from links to be purchased
def checkpurchases(driver, links):
    print("Cross-checking resources to be purchased and those already purchased...")
    driver.get("https://www.ieee.org/profile/otherpurchases/showOtherPurchases.html")

    time.sleep(5)
    purchases = []
    pagelinks = driver.find_elements_by_tag_name("a")

    # Get list of purchased resources
    for pagelink in pagelinks:
        if (pagelink.text == "View/Download"):
            purchases.append(pagelink.get_attribute("id")[20:])

    cartlinks = links.copy()
    for link in links:
        rs = link.rsplit('/')[-1][:-5]

        # compare list of purchases to list of resource links to be added to cart
        for purchase in purchases:
            if (rs == purchase):
                cartlinks.remove(link)

    if (len(links) == len(cartlinks)):
        print("No resource has been purchased from the list of links")
    else:
        print("Resource links reduced from %d to %d" % (len(links), len(cartlinks)))

    return purchases, cartlinks

def checkout(driver):
    driver.get("https://www.ieee.org/cart/public/myCart/page.html")

    # last check to make sure that cart contents are free
    # large delay is needed if there are many items in the cart
    time.sleep(20)
    amount = driver.find_element_by_css_selector("p.total-col-text.float-left.total-col-width span").text
    try:
        assert(amount == "0.00")

        # load checkout page
        print("Free resources verified. Checking out...")
        driver.get("https://www.ieee.org/cart/checkout/page.html")

        # large delay is needed if there are many items in the cart    
        time.sleep(20)

        # scroll terms and conditions checkbox into view
        checkbox = driver.find_element_by_id("terms-conditions")
        driver.execute_script("arguments[0].scrollIntoView();", checkbox)

        # click checkbox
        driver.find_element_by_id("terms-conditions").click()
        time.sleep(0.5)

        # place order
        driver.find_element_by_id("place-order-button2").click()

        print("Purchase finished.")
        time.sleep(10)

        abort = 0
        return abort
    except Exception as e:
        print(e)
        print("Total amount is %s. Aborting..." % (amount))
        abort = 1
    return abort