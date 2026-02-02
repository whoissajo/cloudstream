import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.*
import com.lagradost.cloudstream3.app
import com.lagradost.cloudstream3.utils.AppUtils.parseJson
import com.lagradost.cloudstream3.MainAPI
import com.lagradost.cloudstream3.TvType
import com.lagradost.cloudstream3.SearchResponse
import com.lagradost.cloudstream3.LoadResponse
import com.lagradost.cloudstream3.MainPageRequest
import com.lagradost.cloudstream3.HomePageResponse
import com.lagradost.cloudstream3.HomePageList
import com.lagradost.cloudstream3.SubtitleFile
import com.lagradost.cloudstream3.utils.ExtractorLink
import com.lagradost.cloudstream3.utils.Qualities
import com.lagradost.cloudstream3.utils.ExtractorLinkType
import com.lagradost.cloudstream3.plugins.CloudstreamPlugin
import com.lagradost.cloudstream3.plugins.Plugin
import android.content.Context

@CloudstreamPlugin
class UmarR2Plugin: Plugin() {
    override fun load(context: Context) {
        // All providers should be added here
        registerMainAPI(UmarR2Provider())
    }
}

/**
 * UmarR2Provider
 * Streams direct video files from a Cloudflare R2 JSON API.
 */
class UmarR2Provider : MainAPI() {
    override var name = "UmarR2Provider"
    override var mainUrl = "https://s33.umarbahi.qzz.io"
    override var supportedTypes = setOf(TvType.Movie)

    private val apiUrl = "https://s3.umarbahi.qzz.io/list"

    data class R2File(
        val key: String,
        val streamUrl: String,
        val size: Long? = null
    )

    data class R2Response(
        val files: List<R2File>
    )

    private suspend fun getFiles(): List<R2File> {
        val response = app.get(apiUrl).text
        val data = parseJson<R2Response>(response)
        return data.files.filter { it.key.endsWith(".mp4", ignoreCase = true) || it.key.endsWith(".mkv", ignoreCase = true) }
    }

    override suspend fun getMainPage(page: Int, request: MainPageRequest): HomePageResponse? {
        val files = getFiles()
        val items = files.map { file ->
            newMovieSearchResponse(file.key, file.streamUrl, TvType.Movie) {
                this.posterUrl = null
            }
        }
        return newHomePageResponse(listOf(HomePageList("Latest Files", items)), false)
    }

    override suspend fun search(query: String): List<SearchResponse> {
        val files = getFiles()
        return files.filter { it.key.contains(query, ignoreCase = true) }.map { file ->
            newMovieSearchResponse(file.key, file.streamUrl, TvType.Movie)
        }
    }

    override suspend fun load(url: String): LoadResponse {
        val title = url.substringAfterLast("/")
        return newMovieLoadResponse(title, url, TvType.Movie, url) {
            this.posterUrl = null
            this.plot = "Direct stream from R2: $title"
        }
    }

    override suspend fun loadLinks(
        data: String,
        isCasting: Boolean,
        subtitleCallback: (SubtitleFile) -> Unit,
        callback: (ExtractorLink) -> Unit
    ): Boolean {
        callback(
            newExtractorLink(
                source = "UmarR2",
                name = "R2 Direct",
                url = data,
                type = ExtractorLinkType.VIDEO
            ) {
                this.quality = Qualities.P1080.value
            }
        )
        return true
    }
}
