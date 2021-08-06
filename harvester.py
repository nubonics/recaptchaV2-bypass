from recaptchaV2bypass import RecaptchaV2Bypass


def harvester():
    t = RecaptchaV2Bypass(harvest_mode=True)
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
