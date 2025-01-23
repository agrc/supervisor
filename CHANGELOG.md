# Changelog

## [3.1.1](https://github.com/agrc/supervisor/compare/v3.1.1...v3.1.1) (2025-01-23)


### ⚠ BREAKING CHANGES

* Consolidate project_name into the specific MessageHandlers rather than separate entries for both Supervisor and each MessageDetail object. refs #8.

### Features

* add SendGrid handler ([#11](https://github.com/agrc/supervisor/issues/11)) ([c261e60](https://github.com/agrc/supervisor/commit/c261e607527ff5009494c0858bebafd2c3d289b4))
* always output exceptions to console ([7bafd0a](https://github.com/agrc/supervisor/commit/7bafd0ae63c3d9c02cb63e7e00818651c5f4a4b0))
* basic framework ([b5fc170](https://github.com/agrc/supervisor/commit/b5fc17059c8509d9d18b46027098375415f501b8))
* codecov yml ([7b59dd7](https://github.com/agrc/supervisor/commit/7b59dd7d8c423346e44d5ae7208e44bbdc6bdf4b))
* combine Supervisor and Messenger ([946c883](https://github.com/agrc/supervisor/commit/946c8830b019a9764cba044b0f8101082a7ddb86))
* example implementation ([5c4d745](https://github.com/agrc/supervisor/commit/5c4d745c8440d4d0c9e4bf5c638de69357ac38bd))
* global exception handler stub ([1930ccc](https://github.com/agrc/supervisor/commit/1930ccc0b91b2e9f9d667bb2c0cdd4fe7ce4e01d))
* imports, instantiate smtp internally ([6aefbe5](https://github.com/agrc/supervisor/commit/6aefbe53cbc967dc8cae770213eab451e13b6c2e))
* log path as dict item not parameter ([a1fe327](https://github.com/agrc/supervisor/commit/a1fe3271fb3259261343c9c355d459e251bfd795))
* logger in exception handler, subject prefix ([fc47f7b](https://github.com/agrc/supervisor/commit/fc47f7b1cade19b422fc1963dc2e4e2699a4bba1))
* make error handling optional ([e78f651](https://github.com/agrc/supervisor/commit/e78f6516bffdbf26caf6838395343704a90f5710))
* message as dict, project name in init ([e499fd7](https://github.com/agrc/supervisor/commit/e499fd77f91ffad14981be7396683fcd7010b0ed))
* message details as an object, not dict ([03b6bad](https://github.com/agrc/supervisor/commit/03b6bad1b4fd6cfade0b5878304230576d35758a))
* pass version from client ([57539b6](https://github.com/agrc/supervisor/commit/57539b69ff1834462d75bf9c8567063c9384e927))
* require requests ([953ed1c](https://github.com/agrc/supervisor/commit/953ed1ca0ce73ea7b59acd5dbf34c0cfeaecd03a))
* start work on attachments ([cb5c424](https://github.com/agrc/supervisor/commit/cb5c424549dff9a2bb27ecef73536ba39a3496a1))
* test addresses and attachments ([b75ce9b](https://github.com/agrc/supervisor/commit/b75ce9b198ee0dd76770859a1760a6968835045f))
* test email settings checks ([affba7c](https://github.com/agrc/supervisor/commit/affba7cf44b3cffd2897df72e308dca3b83962d1))
* test message generation ([a4abb27](https://github.com/agrc/supervisor/commit/a4abb274a8c7bd861bcd763ea6e091bb43467a65))
* testing console handler ([1576b5f](https://github.com/agrc/supervisor/commit/1576b5f79f09470777b73d758a90156e5e76d402))
* update example with log, subject prefix ([332f4c5](https://github.com/agrc/supervisor/commit/332f4c580c167cee53dcadec309329ab90d88b53))
* updated dev tools, fix: non-breaking requests version ([7e19288](https://github.com/agrc/supervisor/commit/7e19288a48692501eb0c792f9f910c90a7c43389))


### Bug Fixes

* add hostname to error report, close [#2](https://github.com/agrc/supervisor/issues/2) ([3c9d405](https://github.com/agrc/supervisor/commit/3c9d40569c575bac5eced49db2e5c46dfb916f7f))
* add null checks to email server variables ([2b7c5f2](https://github.com/agrc/supervisor/commit/2b7c5f237bb29371824a7ab9b6c024bd6868ad15))
* body will always be a string ([0f83c37](https://github.com/agrc/supervisor/commit/0f83c37de9f2c89925adb79b4d47718570b4dd33))
* bullet time ([3448100](https://github.com/agrc/supervisor/commit/34481006e3f7de0cd13df624074832dbef49aaa0))
* cleanup, version in email conditional ([07e1aaa](https://github.com/agrc/supervisor/commit/07e1aaaa4268af1fe35da80047c16f2bdb466a1f))
* dechaining for testing ([623ff54](https://github.com/agrc/supervisor/commit/623ff54285dd5235e937cb26d0b625f8e5efb55d))
* docs, send project name for version, close [#3](https://github.com/agrc/supervisor/issues/3) ([8ffb99a](https://github.com/agrc/supervisor/commit/8ffb99a1708b0ecb759b3bad7f42f4a3a82612b2))
* email handler default client name, version ([97f6eda](https://github.com/agrc/supervisor/commit/97f6eda9cd76511b565f9876a3099d57e1fb3deb))
* emtpying the quiver (and the string) ([2ea6610](https://github.com/agrc/supervisor/commit/2ea6610dcf36bb3d10450b40bc59b6daf5732835))
* exceptions use MessageDetails object ([0c29a5a](https://github.com/agrc/supervisor/commit/0c29a5adcf4494ca10bd4fdd25f62f115bfcc5b2))
* make a true closure ([b6dedd8](https://github.com/agrc/supervisor/commit/b6dedd8828442bf6a4873dd3f6fa9f4123fa419a))
* make log_file a generic attachment ([2a2cb56](https://github.com/agrc/supervisor/commit/2a2cb5695ece0d0e13769cf0c3e1333943af9223))
* remove comment ([552cd06](https://github.com/agrc/supervisor/commit/552cd06780162405ee8a6148ca051d8f21034a5a))
* spelling is fun ([b20eaaa](https://github.com/agrc/supervisor/commit/b20eaaa3ecb7ff2d99e220e88f73f397aa9bcacc))
* warn on settings errors instead of logging ([3fece66](https://github.com/agrc/supervisor/commit/3fece66e144f302f69510183f8e7f07f8eb8ccac))
* warning verbiage ([8f5e219](https://github.com/agrc/supervisor/commit/8f5e219c522d9df734fa3e2fd1596c9e00c5a4a5))


### Dependencies

* **dev:** bump the major-dependencies group with 3 updates ([93e392a](https://github.com/agrc/supervisor/commit/93e392a5781c0b8a66dc7d47728596d8862eeb15))
* **dev:** update pytest-cov requirement from &lt;6.0,&gt;=4.1 to &gt;=4.1,&lt;7.0 ([c38622b](https://github.com/agrc/supervisor/commit/c38622be8103b4083acebf0c272ac88fd9571709))
* pytest-pylint ([58a35a4](https://github.com/agrc/supervisor/commit/58a35a457579a1ed3929a116c909d00518cc5f34))
* q3 dependency updates ([ccc706d](https://github.com/agrc/supervisor/commit/ccc706d61a37d3aa4051b23b8650d4d953ab764c))


### Documentation

* API documentation ([24ec332](https://github.com/agrc/supervisor/commit/24ec332e9c154d033ee5e15685f2833982551169))
* clarification ([89340be](https://github.com/agrc/supervisor/commit/89340be45bc39d23d4d112a52acd342b33dff091))
* code example ([3cfdfae](https://github.com/agrc/supervisor/commit/3cfdfae68f5f63ad689d023ab521c05613dad2af))
* correct badges ([03c85c9](https://github.com/agrc/supervisor/commit/03c85c95169c066918eefb27753a34f304bf7832))
* didn't catch all the old stuff ([fae9621](https://github.com/agrc/supervisor/commit/fae962131531504164bfd75404cf6da97ac99a76))
* document message_details ([243cf6f](https://github.com/agrc/supervisor/commit/243cf6f8a59ca07c8af5916fd63d5f217ef0f88a))
* formatting, reference in readme ([d849ad0](https://github.com/agrc/supervisor/commit/d849ad0b760c431b53673c116714420bc706643b))
* helps to be correct ([bfa0f85](https://github.com/agrc/supervisor/commit/bfa0f85211ba542b366d4ab956f17b090778202f))
* message handlers ([eb41276](https://github.com/agrc/supervisor/commit/eb41276c8e8ab433e27545e68a56ad004eb5044d))
* minor niggles ([c032b07](https://github.com/agrc/supervisor/commit/c032b07cfab4c863331ab6056840be6ce14e2e45))
* models ([68deb18](https://github.com/agrc/supervisor/commit/68deb181d92cd76a73e64ea750c7070ce7000690))
* now available on pypi ([d8b264d](https://github.com/agrc/supervisor/commit/d8b264d7bcc9141cfe1ab687a450ed9e40471c79))
* pypi name ([6bcd191](https://github.com/agrc/supervisor/commit/6bcd1910688137fb3601664bf5c70a3d4b27ae2f))
* rename example implementation ([855b1c2](https://github.com/agrc/supervisor/commit/855b1c2ef9a3d8d2689124415d9f18427375afe7))
* send pizza ([177cae9](https://github.com/agrc/supervisor/commit/177cae92dd6e88d64dd60a226fd67dd6f624a304))
* update name ([8d0f3a4](https://github.com/agrc/supervisor/commit/8d0f3a447e39aa46f92afa5346700a9b88b66233))
* update project name in install docs ([b9ab82c](https://github.com/agrc/supervisor/commit/b9ab82c5de1ff2ebabc00c5d0256939f7bd4e852))
* update readme ([44c1530](https://github.com/agrc/supervisor/commit/44c1530f50baa9f6c4eab5c6c7ac7487b791e7c1))
* updating pypi ([929fe7d](https://github.com/agrc/supervisor/commit/929fe7df394ad0acb01facd041ba5e2b55b41e80))

## [3.1.1](https://github.com/agrc/supervisor/compare/3.1.0...v3.1.1) (2025-01-23)


### Features

* updated dev tools, fix: non-breaking requests version ([7e19288](https://github.com/agrc/supervisor/commit/7e19288a48692501eb0c792f9f910c90a7c43389))


### Dependencies

* **dev:** update pytest-cov requirement from &lt;6.0,&gt;=4.1 to &gt;=4.1,&lt;7.0 ([c38622b](https://github.com/agrc/supervisor/commit/c38622be8103b4083acebf0c272ac88fd9571709))


### Documentation

* update project name in install docs ([b9ab82c](https://github.com/agrc/supervisor/commit/b9ab82c5de1ff2ebabc00c5d0256939f7bd4e852))
