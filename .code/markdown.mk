sources := $(wildcard *.md)
targets := $(patsubst %.md,%.html,$(sources))

code_dir := .code

asset_dir := .markdown
assets := $(wildcard $(asset_dir)/*)


all: markdown $(assets)

markdown: $(targets)


%.html: %.md $(assets)
	if true; then \
		title=`echo "$<" | tr '_' ' ' | sed "s/\..*$$//g"`; \
		cat ${asset_dir}/top.html | sed "s/@@PAGETITLE@@/$$title/g" > "$@"; \
		if [ -f ".markdown/style.css" ]; then \
			cat ".markdown/style.css" >> "$@"; \
		else \
			cat ${asset_dir}/style.css >> "$@"; \
		fi; \
		cat ${asset_dir}/middle.html >> "$@"; \
		markdown < "$<" >> "$@"; \
		cat ${asset_dir}/bottom.html >> "$@"; \
		if echo "$<" | grep "^ICFJ" >/dev/null 2>&1; then \
			${code_dir}/convert.py --pm-lezione "$@"; \
		else \
			${code_dir}/convert.py --pm "$@"; \
		fi; \
	fi


clean:
	rm -f $(targets)

.PHONY: all markdown clean
