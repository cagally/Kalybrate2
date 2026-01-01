(defproject data-transformer "0.1.0-SNAPSHOT"
  :description "A comprehensive library for parsing and transforming nested data structures"
  :url "https://github.com/yourusername/data-transformer"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [[org.clojure/clojure "1.10.3"]
                 [prismatic/schema "1.1.12"]
                 [metosin/malli "0.8.0"]]
  :plugins [[lein-cljfmt "0.8.0"]
            [lein-kibit "0.1.8"]]
  :source-paths ["src"]
  :test-paths ["test"]
  :profiles {:dev {:dependencies [[org.clojure/test.check "1.1.1"]]
                   :plugins [[lein-cloverage "1.2.2"]]}})
