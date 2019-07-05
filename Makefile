# Makefile for QuickOSM

i18n_1_prepare:
	@echo Updating strings locally 1/4
	@./update_strings.sh fr de en fi it nl ru zh-TW

i18n_2_push:
	@echo Push strings to Transifex 2/4
	@tx push -s

i18n_3_pull:
	@echo Pull strings from Transifex 3/4
	@tx pull -a

i18n_4_compile:
	@echo Compile TS files to QM 4/4
	@lrelease i18n/QuickOSM_fr.ts -qm i18n/QuickOSM_fr.qm
	@lrelease i18n/QuickOSM_de.ts -qm i18n/QuickOSM_de.qm
	@lrelease i18n/QuickOSM_fi.ts -qm i18n/QuickOSM_fi.qm
	@lrelease i18n/QuickOSM_it.ts -qm i18n/QuickOSM_it.qm
	@lrelease i18n/QuickOSM_nl.ts -qm i18n/QuickOSM_nl.qm
	@lrelease i18n/QuickOSM_ru.ts -qm i18n/QuickOSM_ru.qm
	@lrelease i18n/QuickOSM_zh-TW.ts -qm i18n/QuickOSM_zh-TW.qm

main_window:
	@echo pyuic5 main_window.ui > ui/main_window.py
	@pyuic5 ui/main_window.ui > ui/main_window.py

quick_query:
	@echo pyuic5 ui/quick_query.ui > ui/quick_query.py
	@pyuic5 ui/quick_query.ui > ui/quick_query.py

osm_file:
	@echo pyuic5 ui/osm_file.ui > ui/osm_file.py
	@pyuic5 ui/osm_file.ui > ui/osm_file.py

query:
	@echo pyuic5 ui/query.ui > ui/query.py
	@pyuic5 ui/query.ui > ui/query.py

save_query:
	@echo pyuic5 ui/save_query.ui > ui/save_query.py
	@pyuic5 ui/save_query.ui > ui/save_query.py

generate_ui: main_window quick_query osm_file query save_query
