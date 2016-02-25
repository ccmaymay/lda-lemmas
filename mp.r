require(jsonlite)

mp <- function(results.path, key.path) {
    results <- read.csv(results.path, header=T)
    answer.col.idx <- which(grepl('^Answer.', colnames(results)))
    if (length(answer.col.idx) != 1) {
        stop('too many answers')
    }
    results.va <- lapply(as.list(results$Input.var_arrays),
                         function(x) {fromJSON(as.character(x))})

    key <- read.delim(key.path, header=T)
    key.ids <- vapply(1:dim(results)[1],
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
                    experiment=factor(key$experiment[key.ids]))
    d$correct <- d$ans.human == d$ans.model
    d$total <- rep(1, dim(d)[1])

    d.agg <- aggregate(cbind(correct, total) ~ experiment,
                       data=d,
                       FUN=sum)
    d.agg$mp <- d.agg$correct / d.agg$total

    d.agg
}

results.path <- 'wiki-ru-dll.big.results.nocr.csv'
key.path <- 'wiki-ru-dll-lda-trunc50-big.key.tsv'
print(mp(results.path, key.path))
