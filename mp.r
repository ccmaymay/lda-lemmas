require(jsonlite)
require(reshape2)

mp <- function(results.path, key.path) {
    # load results, find answer column
    results <- read.csv(results.path, header=T)
    results.va <- lapply(as.list(results$Input.var_arrays),
                         function(x) {fromJSON(as.character(x))})
    answer.col.idx <- which(grepl('^Answer.', colnames(results)))
    if (length(answer.col.idx) != 1) {
        stop('too many answers')
    }

    # load key, sort by wl_id from results
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
    key <- key[key.ids,]

    # aggregate data
    d <- data.frame(ans.human=results[,answer.col.idx],
                    ans.model=key$intruder.idx,
                    experiment=key$experiment)
    d$correct <- d$ans.human == d$ans.model
    ex.levels <- levels(d$experiment)
    ex.dll <- grepl(':dll', as.character(ex.levels))
    ex.level.dll <- ex.levels[which(ex.dll)[1]]
    ex.level.dl <- ex.levels[which(!ex.dll)[1]]
    d.tab <- table(factor(d$experiment,
                          levels=c(ex.level.dll, ex.level.dl)),
                   factor(d$correct,
                          levels=c(TRUE, FALSE)))

    # compute model precision CI
    cat('prop 1:', as.character(ex.level.dll), '\n')
    cat('prop 2:', as.character(ex.level.dl), '\n')
    ci <- prop.test(d.tab,
                    conf.level=0.99,
                    alternative='greater',
                    correct=F)
    print(ci)
}

results.prefix <- 'wiki.ru.dll.big.'
results.suffix <- '.nocr.csv'
key.prefix <- 'wiki.ru.dll.big.'
key.suffix <- '.tsv'
for (i in c(1,3,5,7)) {
    results.path <- paste(results.prefix, i, results.suffix, sep='')
    key.path <- paste(key.prefix, i, key.suffix, sep='')
    ci <- mp(results.path, key.path)
}
