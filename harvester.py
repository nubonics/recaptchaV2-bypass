from bypass import TFRecaptcha


def harvester():
    t = TFRecaptcha()
    t.init_tf()
    t.init_browser()

    while True:
        try:
            t.open_test_recaptcha()
            t.generate_recaptcha_classes()
        except:
            t.init_browser()


if __name__ == '__main__':
    harvester()
