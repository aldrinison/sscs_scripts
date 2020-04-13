import sscs

# generate webdriver
driver = sscs.init()

# Wait for user to sign-in
input("Sign in using your IEEE account (you can make a free account).\n Once signed in and the redirected page has fully loaded, press ENTER to proceed: ")

# add primary address
sscs.addaddress(driver)

# get full links to resources
links = sscs.parselinks()

# cross-check links to already purchased resources
purchases, cartlinks = sscs.checkpurchases(driver, links)

# automatic addition to cart
sscs.autoaddtocart(driver, cartlinks)

print("Script finished!")