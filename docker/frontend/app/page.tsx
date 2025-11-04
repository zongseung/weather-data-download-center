"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Download,
  ArrowLeft,
  CheckCircle2,
  Cloud,
  CloudRain,
  CloudSun,
  FileText,
  Calendar,
  Info,
  ChevronDown,
} from "lucide-react"

const rawBackendBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").trim()
const normalizedBackendBaseUrl = rawBackendBaseUrl.replace(/\/$/, "")

const BACKEND_API_BASE =
  normalizedBackendBaseUrl === ""
    ? "/api"
    : normalizedBackendBaseUrl.endsWith("/api")
      ? normalizedBackendBaseUrl
      : `${normalizedBackendBaseUrl}/api`

const DEFAULT_FORECAST_TYPES = ["단기예보", "초단기실황", "초단기예보"]

const forecastTypeIcons: Record<string, any> = {
  "단기예보": Cloud,
  "초단기예보": CloudRain,
  "초단기실황": CloudSun,
}

const forecastTypeDescriptions: Record<string, string> = {
  "단기예보": "단기예보는 3~5일 정도의 날씨를 예측하는 예보이고, 초단기예보는 6시간 이내의 가까운 미래 날씨를 예측하는 예보",
  "초단기예보": "예보 시점부터 6시간까지의 가까운 날씨 변화를 예측합니다.",
  "초단기실황": "현재 날씨 상태를 5km 격자 단위로 보여주는, 사람의 관측(AWS, Automatic Weather Station)값을 기반으로 한 실시간 정보",
}

type Step = "forecast" | "level1" | "level2" | "level3" | "variables" | "files"

interface Variable {
  name: string
  file_count: number
  path: string
}

interface FileInfo {
  filename: string
  size: number
  size_mb: number
  start_date: string
  end_date: string
  modified: number
}

interface FilePreviewData {
  file: FileInfo
  lines: string[]
  encoding: string
  line_count: number
  requested_lines: number
}

interface NasForecastTypeSummary {
  name: string
  city_count?: number
  district_count?: number
  town_count?: number
}

interface NasSummary {
  nas_path: string
  nas_available: boolean
  forecast_types: NasForecastTypeSummary[]
}

export default function WeatherDataPlatform() {
  const [currentStep, setCurrentStep] = useState<Step>("forecast")
  const [selectedForecast, setSelectedForecast] = useState<string>("")
  const [selectedLevel1, setSelectedLevel1] = useState<string>("")
  const [selectedLevel2, setSelectedLevel2] = useState<string>("")
  const [selectedLevel3, setSelectedLevel3] = useState<string>("")
  const [selectedVariable, setSelectedVariable] = useState<string>("")

  const [forecastTypes, setForecastTypes] = useState<string[]>(DEFAULT_FORECAST_TYPES)
  const [level1Options, setLevel1Options] = useState<string[]>([])
  const [level2Options, setLevel2Options] = useState<string[]>([])
  const [level3Options, setLevel3Options] = useState<string[]>([])
  const [variables, setVariables] = useState<Variable[]>([])
  const [files, setFiles] = useState<FileInfo[]>([])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>("")
  const [nasSummary, setNasSummary] = useState<NasSummary | null>(null)
  const [showNasInfo, setShowNasInfo] = useState(false)
  const [nasSummaryLoading, setNasSummaryLoading] = useState(false)
  const [nasSummaryError, setNasSummaryError] = useState("")
  const [selectedFilePreview, setSelectedFilePreview] = useState<FilePreviewData | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string>("")

  // 지역코드 데이터 가져오기
  const [regionData, setRegionData] = useState<any[]>([])

  useEffect(() => {
    const fetchRegionData = async () => {
      try {
        setLoading(true)
        const response = await fetch(
          "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/%E1%84%8C%E1%85%B5%E1%84%8B%E1%85%A7%E1%86%A8%E1%84%8F%E1%85%A9%E1%84%83%E1%85%B3-xrsyvxgfV3iHpORYkKc288guJ3R5m6.csv",
        )
        const text = await response.text()
        const lines = text.split("\n")

        const data: any[] = lines
          .slice(1)
          .map((line) => {
            const values = line.split(",")
            return {
              Level1: values[0]?.trim() || "",
              Level2: values[1]?.trim() || "",
              Level3: (values[2]?.trim() || "").replace(/·/g, "."),
              ReqList_Last: values[3]?.trim() || "",
            }
          })
          .filter((item) => item.Level1)

        setRegionData(data)

        // NAS에서 실제 예보 유형 가져오기
        const nasData = await fetch(`${BACKEND_API_BASE}/nas/forecast-types`).then((res) => res.json())
        const nasForecastTypes = Array.isArray(nasData.forecast_types)
          ? nasData.forecast_types
              .map((ft: any) => (typeof ft === "string" ? ft : ft?.name))
              .filter((name: string | undefined): name is string => Boolean(name))
          : []

        const mergedForecastTypes = [...DEFAULT_FORECAST_TYPES]
        nasForecastTypes.forEach((type: string) => {
          if (!mergedForecastTypes.includes(type)) {
            mergedForecastTypes.push(type)
          }
        })

        setForecastTypes(mergedForecastTypes)
      } catch (error) {
        console.error("[v0] Error fetching data:", error)
        setForecastTypes((prev) => (prev.length ? prev : DEFAULT_FORECAST_TYPES))
        setError("데이터를 불러오는데 실패했습니다.")
      } finally {
        setLoading(false)
      }
    }
    fetchRegionData()
  }, [])

  useEffect(() => {
    if (currentStep !== "forecast") {
      setShowNasInfo(false)
    }
  }, [currentStep])

  useEffect(() => {
    if (!showNasInfo || nasSummary || nasSummaryLoading || nasSummaryError) {
      return
    }

    const fetchNasSummary = async () => {
      try {
        setNasSummaryLoading(true)
        setNasSummaryError("")
        const response = await fetch(`${BACKEND_API_BASE}/nas/data-summary`)
        if (!response.ok) {
          throw new Error("Failed to fetch NAS summary")
        }
        const summaryData = await response.json()
        if (summaryData?.nas_path) {
          setNasSummary(summaryData as NasSummary)
        } else {
          setNasSummary(null)
          setNasSummaryError("NAS 정보를 찾을 수 없습니다.")
        }
      } catch (err) {
        console.error("[v0] Error fetching NAS summary:", err)
        setNasSummary(null)
        setNasSummaryError("NAS 정보를 불러오는데 실패했습니다.")
      } finally {
        setNasSummaryLoading(false)
      }
    }

    fetchNasSummary()
  }, [showNasInfo, nasSummary, nasSummaryLoading, nasSummaryError])

  // 지역코드 CSV에서 시/도 목록 가져오기
  const fetchLevel1 = (forecastType: string) => {
    const cities = Array.from(new Set(regionData.map((item) => item.Level1))).filter(Boolean).sort()
    setLevel1Options(cities)
  }

  // 지역코드 CSV에서 구/군 목록 가져오기
  const fetchLevel2 = (forecastType: string, city: string) => {
    const districts = Array.from(
      new Set(regionData.filter((item) => item.Level1 === city).map((item) => item.Level2))
    )
      .filter(Boolean)
      .sort()
    setLevel2Options(districts)
  }

  // 지역코드 CSV에서 동/읍/면 목록 가져오기
  const fetchLevel3 = (forecastType: string, city: string, district: string) => {
    const towns = Array.from(
      new Set(
        regionData
          .filter((item) => item.Level1 === city && item.Level2 === district)
          .map((item) => item.Level3)
      )
    )
      .filter(Boolean)
      .sort()
    setLevel3Options(towns)
  }

  // 예보 변수 목록 가져오기
  const fetchVariables = async (forecastType: string, city: string, district: string, town: string) => {
    try {
      setLoading(true)
      const response = await fetch(
        `${BACKEND_API_BASE}/nas/variables?forecast_type=${encodeURIComponent(forecastType)}&city=${encodeURIComponent(city)}&district=${encodeURIComponent(district)}&town=${encodeURIComponent(town)}`
      )
      const data = await response.json()
      setVariables(data.variables)
      setLoading(false)
    } catch (error) {
      console.error("[v0] Error fetching variables:", error)
      setError("예보 변수 목록을 불러오는데 실패했습니다.")
      setLoading(false)
    }
  }

  // 파일 목록 가져오기
  const fetchFiles = async (forecastType: string, city: string, district: string, town: string, variable: string) => {
    try {
      setLoading(true)
      const response = await fetch(
        `${BACKEND_API_BASE}/nas/variable-files?forecast_type=${encodeURIComponent(forecastType)}&city=${encodeURIComponent(city)}&district=${encodeURIComponent(district)}&town=${encodeURIComponent(town)}&variable=${encodeURIComponent(variable)}`
      )
      const data = await response.json()
      setFiles(data.files)
      setSelectedFilePreview(null)
      setPreviewError("")
      setLoading(false)
    } catch (error) {
      console.error("[v0] Error fetching files:", error)
      setError("파일 목록을 불러오는데 실패했습니다.")
      setLoading(false)
    }
  }

  const handleForecastSelect = (forecastName: string) => {
    setSelectedForecast(forecastName)
    fetchLevel1(forecastName)
    setCurrentStep("level1")
  }

  const handleLevel1Select = (level1: string) => {
    setSelectedLevel1(level1)
    fetchLevel2(selectedForecast, level1)
    setCurrentStep("level2")
  }

  const handleLevel2Select = (level2: string) => {
    setSelectedLevel2(level2)
    fetchLevel3(selectedForecast, selectedLevel1, level2)
    setCurrentStep("level3")
  }

  const handleLevel3Select = (level3: string) => {
    setSelectedLevel3(level3)
    fetchVariables(selectedForecast, selectedLevel1, selectedLevel2, level3)
    setCurrentStep("variables")
  }

  const handleVariableSelect = (variable: string) => {
    setSelectedVariable(variable)
    setSelectedFilePreview(null)
    setPreviewError("")
    fetchFiles(selectedForecast, selectedLevel1, selectedLevel2, selectedLevel3, variable)
    setCurrentStep("files")
  }

  const handleToggleNasInfo = () => {
    if (showNasInfo) {
      setShowNasInfo(false)
      return
    }
    setNasSummaryError("")
    setShowNasInfo(true)
  }

  const handleFilePreview = async (file: FileInfo) => {
    if (selectedFilePreview?.file.filename === file.filename) {
      setSelectedFilePreview(null)
      setPreviewError("")
      return
    }

    setPreviewLoading(true)
    setPreviewError("")

    try {
      const url = `${BACKEND_API_BASE}/nas/file-preview?forecast_type=${encodeURIComponent(selectedForecast)}&city=${encodeURIComponent(selectedLevel1)}&district=${encodeURIComponent(selectedLevel2)}&town=${encodeURIComponent(selectedLevel3)}&variable=${encodeURIComponent(selectedVariable)}&filename=${encodeURIComponent(file.filename)}&lines=40`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error("Failed to fetch preview")
      }

      const data = await response.json()

      setSelectedFilePreview({
        file,
        lines: Array.isArray(data.lines) ? data.lines : [],
        encoding: data.encoding || "",
        line_count: data.line_count || 0,
        requested_lines: data.requested_lines || 0,
      })
    } catch (err) {
      console.error("[v0] Error fetching file preview:", err)
      setPreviewError("파일 미리보기를 불러오는데 실패했습니다.")
      setSelectedFilePreview(null)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleDownload = (file: FileInfo) => {
    const url = `${BACKEND_API_BASE}/nas/download?forecast_type=${encodeURIComponent(selectedForecast)}&city=${encodeURIComponent(selectedLevel1)}&district=${encodeURIComponent(selectedLevel2)}&town=${encodeURIComponent(selectedLevel3)}&variable=${encodeURIComponent(selectedVariable)}&filename=${encodeURIComponent(file.filename)}`

    const link = document.createElement("a")
    link.href = url
    link.download = file.filename
    link.target = "_self"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleBack = () => {
    if (currentStep === "files") {
      setCurrentStep("variables")
      setSelectedVariable("")
      setFiles([])
      setSelectedFilePreview(null)
      setPreviewError("")
    } else if (currentStep === "variables") {
      setCurrentStep("level3")
      setSelectedLevel3("")
      setVariables([])
    } else if (currentStep === "level3") {
      setCurrentStep("level2")
      setSelectedLevel2("")
      setLevel3Options([])
    } else if (currentStep === "level2") {
      setCurrentStep("level1")
      setSelectedLevel1("")
      setLevel2Options([])
    } else if (currentStep === "level1") {
      setCurrentStep("forecast")
      setSelectedForecast("")
      setLevel1Options([])
    }
  }

  if (loading && currentStep === "forecast") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-lg text-muted-foreground">데이터를 불러오는 중...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="space-y-3 text-center md:text-left">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground tracking-tight">
            기상 데이터 다운로드 플랫폼
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl">
            NAS 서버에서 수집된 기상 데이터를 조회하고 다운로드하세요
          </p>
        </div>

        {currentStep !== "forecast" && (
          <Card className="border-2 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-sm flex-wrap">
                <span className="text-primary font-semibold text-base">{selectedForecast}</span>
                {selectedLevel1 && (
                  <>
                    <span className="text-muted-foreground">›</span>
                    <span className="text-primary font-semibold text-base">{selectedLevel1}</span>
                  </>
                )}
                {selectedLevel2 && (
                  <>
                    <span className="text-muted-foreground">›</span>
                    <span className="text-primary font-semibold text-base">{selectedLevel2}</span>
                  </>
                )}
                {selectedLevel3 && (
                  <>
                    <span className="text-muted-foreground">›</span>
                    <span className="text-primary font-semibold text-base">{selectedLevel3}</span>
                  </>
                )}
                {selectedVariable && (
                  <>
                    <span className="text-muted-foreground">›</span>
                    <span className="text-primary font-semibold text-base">{selectedVariable}</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {currentStep !== "forecast" && (
          <Button
            onClick={handleBack}
            variant="outline"
            size="lg"
            className="gap-2 border-2 hover:border-primary hover:bg-primary/5 transition-all duration-300 bg-transparent"
          >
            <ArrowLeft className="h-5 w-5" />
            이전으로
          </Button>
        )}

        {error && (
          <Card className="border-2 border-destructive">
            <CardContent className="p-4">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Step 1: Forecast Type Selection */}
        {currentStep === "forecast" && showNasInfo ? (
          <div className="space-y-6">
            <Button
              onClick={() => setShowNasInfo(false)}
              variant="outline"
              size="lg"
              className="gap-2 border-2 hover:border-primary hover:bg-primary/5 transition-all duration-300 bg-transparent"
            >
              <ArrowLeft className="h-5 w-5" />
              예보 선택으로 돌아가기
            </Button>

            <Card className="border-2 border-primary/20 bg-card/40 backdrop-blur-sm">
              <CardHeader className="pb-4">
                <div className="flex flex-col gap-1">
                  <CardTitle className="text-xl text-primary">현재 NAS 정보</CardTitle>
                  <CardDescription className="text-base text-muted-foreground">
                    마운트된 NAS 경로와 데이터 보유 현황을 확인하세요
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {nasSummaryLoading ? (
                  <p className="text-sm text-muted-foreground">NAS 정보를 불러오는 중...</p>
                ) : nasSummaryError ? (
                  <p className="text-sm text-destructive">{nasSummaryError}</p>
                ) : nasSummary ? (
                  <>
                    <div className="flex flex-wrap items-center gap-3 text-sm md:text-base">
                      <span className="font-semibold text-foreground">NAS 경로</span>
                      <span className="px-3 py-1 rounded-full bg-muted text-muted-foreground border border-border">
                        {nasSummary.nas_path}
                      </span>
                    </div>

                    <div className="grid gap-3 md:grid-cols-3">
                      {nasSummary.forecast_types.length > 0 ? (
                        nasSummary.forecast_types.map((forecast) => {
                          const totalLocations =
                            (forecast.city_count || 0) + (forecast.district_count || 0) + (forecast.town_count || 0)
                          return (
                            <Card key={forecast.name} className="border border-border/70 bg-background/60 shadow-sm">
                              <CardHeader className="pb-2">
                                <CardTitle className="text-lg text-foreground">{forecast.name}</CardTitle>
                                <CardDescription className="text-sm text-muted-foreground">
                                  총 {totalLocations.toLocaleString()}개 행정 구역 데이터
                                </CardDescription>
                              </CardHeader>
                              <CardContent className="text-sm text-muted-foreground space-y-1">
                                <div className="flex justify-between">
                                  <span>시/도</span>
                                  <span className="font-medium text-foreground">{(forecast.city_count || 0).toLocaleString()}곳</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>구/군</span>
                                  <span className="font-medium text-foreground">{(forecast.district_count || 0).toLocaleString()}곳</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>동/읍/면</span>
                                  <span className="font-medium text-foreground">{(forecast.town_count || 0).toLocaleString()}곳</span>
                                </div>
                              </CardContent>
                            </Card>
                          )
                        })
                      ) : (
                        <div className="col-span-full text-sm text-muted-foreground">
                          NAS에 예보 데이터가 없습니다. 데이터를 수집한 후 다시 시도하세요.
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">NAS 정보가 없습니다.</p>
                )}
              </CardContent>
            </Card>
          </div>
        ) : (
          <>
            {currentStep === "forecast" && (
              <div className="space-y-6">
                <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
                  <CardHeader className="pb-4">
                    <div className="flex items-center gap-3">
                      <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-xl">
                        1
                      </div>
                      <div>
                        <CardTitle className="text-2xl text-primary">예보 유형 선택</CardTitle>
                        <CardDescription className="text-base mt-1">
                          조회할 데이터의 예보 유형을 선택하세요
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>

                <div className="flex justify-end">
                  <Button
                    onClick={handleToggleNasInfo}
                    variant="outline"
                    className="ml-auto gap-2 border-2 hover:border-primary hover:bg-primary/5 transition-colors"
                  >
                    <Info className="h-4 w-4" />
                    NAS 정보 보기
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </div>

                <div className="grid gap-6 md:grid-cols-3">
                  {forecastTypes.map((type) => {
                    const Icon = forecastTypeIcons[type] || Cloud
                    return (
                      <Card
                        key={type}
                        className="border-2 hover:border-primary transition-all duration-300 cursor-pointer hover:shadow-xl hover:scale-105 group bg-card"
                        onClick={() => handleForecastSelect(type)}
                      >
                        <CardHeader className="space-y-4">
                          <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                            <Icon className="h-8 w-8 text-primary" />
                          </div>
                          <div>
                            <CardTitle className="text-primary text-2xl mb-2">{type}</CardTitle>
                            <CardDescription className="text-base leading-relaxed">
                              {forecastTypeDescriptions[type] || "NAS 서버에서 수집된 기상 데이터"}
                            </CardDescription>
                          </div>
                        </CardHeader>
                      </Card>
                    )
                  })}
                </div>
              </div>
            )}
          </>
        )}

        {!(currentStep === "forecast" && showNasInfo) && (
          <>
            {/* Step 2-4: 지역 선택 (동일 패턴) */}
            {currentStep === "level1" && (
              <div className="space-y-8">
                <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
                  <CardHeader className="pb-4">
                    <div className="flex items-center gap-3">
                      <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-xl">
                        2
                      </div>
                      <div>
                        <CardTitle className="text-2xl text-primary">시/도 선택</CardTitle>
                        <CardDescription className="text-base mt-1">
                          데이터를 조회할 시/도를 선택하세요
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                </Card>

                <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-5">
                  {loading ? (
                    <p className="col-span-full text-center text-muted-foreground">로딩 중...</p>
                  ) : (
                    level1Options.map((level1) => (
                      <Card
                        key={level1}
                        className="border-2 hover:border-primary transition-all duration-300 cursor-pointer hover:shadow-lg hover:scale-105 group bg-card"
                        onClick={() => handleLevel1Select(level1)}
                      >
                        <CardContent className="p-6 flex items-center justify-center min-h-[100px]">
                          <p className="text-center font-semibold text-foreground text-lg group-hover:text-primary transition-colors">
                            {level1}
                          </p>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            )}

            {currentStep === "level2" && (
          <div className="space-y-8">
            <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-xl">
                    3
                  </div>
                  <div>
                    <CardTitle className="text-2xl text-primary">구/군 선택</CardTitle>
                    <CardDescription className="text-base mt-1">{selectedLevel1}의 구/군을 선택하세요</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-5">
              {loading ? (
                <p className="col-span-full text-center text-muted-foreground">로딩 중...</p>
              ) : (
                level2Options.map((level2) => (
                  <Card
                    key={level2}
                    className="border-2 hover:border-primary transition-all duration-300 cursor-pointer hover:shadow-lg hover:scale-105 group bg-card"
                    onClick={() => handleLevel2Select(level2)}
                  >
                    <CardContent className="p-6 flex items-center justify-center min-h-[100px]">
                      <p className="text-center font-semibold text-foreground text-lg group-hover:text-primary transition-colors">
                        {level2}
                      </p>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {currentStep === "level3" && (
          <div className="space-y-8">
            <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-xl">
                    4
                  </div>
                  <div>
                    <CardTitle className="text-2xl text-primary">동/읍/면 선택</CardTitle>
                    <CardDescription className="text-base mt-1">
                      {selectedLevel1} {selectedLevel2}의 동/읍/면을 선택하세요
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-5">
              {loading ? (
                <p className="col-span-full text-center text-muted-foreground">로딩 중...</p>
              ) : (
                level3Options.map((level3) => (
                  <Card
                    key={level3}
                    className="border-2 hover:border-primary transition-all duration-300 cursor-pointer hover:shadow-lg hover:scale-105 group bg-card"
                    onClick={() => handleLevel3Select(level3)}
                  >
                    <CardContent className="p-6 flex items-center justify-center min-h-[100px]">
                      <p className="text-center font-semibold text-foreground text-lg group-hover:text-primary transition-colors">
                        {level3}
                      </p>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {/* Step 5: Variable Selection */}
        {currentStep === "variables" && (
          <div className="space-y-8">
            <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-xl">
                    5
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-2xl text-primary">예보 변수 선택</CardTitle>
                    <CardDescription className="text-base mt-1">
                      조회할 예보 변수를 선택하세요
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-primary">{variables.length}</p>
                    <p className="text-sm text-muted-foreground">개 변수</p>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
              {loading ? (
                <p className="col-span-full text-center text-muted-foreground">로딩 중...</p>
              ) : (
                variables.map((variable) => (
                  <Card
                    key={variable.name}
                    className="border-2 hover:border-primary transition-all duration-300 cursor-pointer hover:shadow-lg hover:scale-105 bg-card"
                    onClick={() => handleVariableSelect(variable.name)}
                  >
                    <CardContent className="p-6 space-y-2">
                      <p className="font-semibold text-lg text-foreground">{variable.name}</p>
                      <p className="text-sm text-muted-foreground">{variable.file_count}개 파일</p>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {/* Step 6: File List */}
        {currentStep === "files" && (
          <div className="space-y-8">
            <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-xl">
                    6
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-2xl text-primary">파일 선택 및 다운로드</CardTitle>
                    <CardDescription className="text-base mt-1">
                      다운로드할 파일을 선택하세요
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-primary">{files.length}</p>
                    <p className="text-sm text-muted-foreground">개 파일</p>
                  </div>
                </div>
              </CardHeader>
            </Card>

            <div className="space-y-4">
              {loading ? (
                <p className="text-center text-muted-foreground">로딩 중...</p>
              ) : (
                files.map((file) => {
                  const isActive = selectedFilePreview?.file.filename === file.filename
                  return (
                    <Card
                      key={file.filename}
                      onClick={() => handleFilePreview(file)}
                      className={`border-2 transition-all duration-300 bg-card cursor-pointer ${
                        isActive ? "border-primary shadow-lg" : "border-border"
                      } hover:border-primary hover:shadow-xl`}
                    >
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1">
                          <FileText className="h-10 w-10 text-primary" />
                          <div className="space-y-1">
                            <p className="font-semibold text-lg">{file.filename}</p>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                {file.start_date} ~ {file.end_date}
                              </span>
                              <span>{file.size_mb} MB</span>
                            </div>
                          </div>
                        </div>
                        <Button
                          onClick={(event) => {
                            event.stopPropagation()
                            handleDownload(file)
                          }}
                          size="lg"
                          className="bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-300"
                        >
                          <Download className="h-5 w-5 mr-2" />
                          다운로드
                        </Button>
                      </div>
                    </CardContent>
                    </Card>
                  )
                })
              )}
            </div>

            {previewLoading && (
              <Card className="border-2 border-primary/30 bg-card/40">
                <CardContent className="p-6 text-sm text-muted-foreground">파일 미리보기를 불러오는 중...</CardContent>
              </Card>
            )}

            {previewError && (
              <Card className="border-2 border-destructive/50 bg-destructive/10">
                <CardContent className="p-6 text-sm text-destructive">{previewError}</CardContent>
              </Card>
            )}

            {selectedFilePreview && !previewLoading && (
              <Card className="border-2 border-primary bg-background/80">
                <CardHeader className="pb-2">
                  <div className="flex flex-col gap-1">
                    <CardTitle className="text-xl text-primary">파일 미리보기</CardTitle>
                    <CardDescription className="text-sm text-muted-foreground">
                      {selectedFilePreview.file.filename} · 인코딩 {selectedFilePreview.encoding || "알 수 없음"}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    <span>표시된 줄 수: {selectedFilePreview.line_count}/{selectedFilePreview.requested_lines}</span>
                    <span>파일 크기: {selectedFilePreview.file.size_mb} MB</span>
                  </div>
                  <div className="rounded-lg border border-border bg-card/70 p-4 max-h-96 overflow-auto">
                    <pre className="whitespace-pre-wrap text-sm leading-6 text-foreground">
                      {selectedFilePreview.lines.length > 0
                        ? selectedFilePreview.lines.join("\n")
                        : "미리보기 데이터를 표시할 수 없습니다."}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </>
    )}
        <p className="text-xs text-muted-foreground text-center pb-4">powered by zongseung</p>
      </div>
    </div>
  )
}
