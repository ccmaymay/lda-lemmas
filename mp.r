require(jsonlite)
require(reshape2)

mp <- function(results.path, key.path) {
    results <- read.csv(results.path, header=T)
    answer.col.idx <- which(grepl('^Answer.', colnames(results)))
    if (length(answer.col.idx) != 1) {
        stop('too many answers')
    }
    results.va <- lapply(as.list(results$Input.var_arrays),
                         function(x) {fromJSON(as.character(x))})

    key <- read.delim(key.path, header=T)
    key.ids <- vapply(1:nrow(results),
                      function(i) {
                          j <- which(key$wl.id ==
                                     results.va[[i]]$wl_id)
                          if (length(j) != 1) {
                              stop('too many id matches')
                          }
                          j
                      },
                      42)

    d <- data.frame(ans.human=results[,answer.col.idx],
                    ans.model=key$intruder.idx[key.ids],
                    experiment=key$experiment[key.ids])
    d$correct <- d$ans.human == d$ans.model

    d.agg <- dcast(d,
                   experiment ~ correct,
                   value.var='correct',
                   fun.aggregate=length)
    d.agg$total <- d.agg[,'TRUE'] + d.agg[,'FALSE']
    d.agg$mp <- d.agg[,'TRUE'] / d.agg$total

    if (nrow(d.agg) != 2) {
        stop('too many rows in aggregated data')
    }
    alt.idx <- which(grepl(':dll', as.character(d.agg$experiment)))
    if (length(alt.idx) != 1 || alt.idx > 2) {
        stop('too many :dll experiments in aggregated data')
    }
    null.idx <- 3 - alt.idx

    d.alt <- subset(d, experiment == d.agg$experiment[alt.idx])
    d.null <- subset(d, experiment == d.agg$experiment[null.idx])

    ex.levels <- levels(d$experiment)
    ex.dll <- grepl(':dll', as.character(ex.levels))
    d.tab <- table(factor(d$experiment,
                          levels=c(ex.levels[which(ex.dll)[1]],
                                   ex.levels[which(!ex.dll)[1]])),
                   factor(d$correct,
                          levels=c(TRUE, FALSE)))
    d.ci <- prop.test(d.tab,
                    conf.level=0.99,
                    alternative='greater',
                    correct=F)

    list(data=d.agg, ci=d.ci)
}

results.prefix <- 'wiki.ru.dll.big.'
results.suffix <- '.nocr.csv'
key.prefix <- 'wiki.ru.dll.big.'
key.suffix <- '.tsv'
for (i in c(1,3,5,7)) {
    results.path <- paste(results.prefix, i, results.suffix, sep='')
    key.path <- paste(key.prefix, i, key.suffix, sep='')
    ret <- mp(results.path, key.path)
    data <- ret$data
    ci <- ret$ci
    cat('\n\n\n')
    print(data)
    print(ci)
}
