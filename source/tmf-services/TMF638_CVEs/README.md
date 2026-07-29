# Analyze CVEs for TMF638 Service



## CVEs in existing docker image (Canvas-Info-Service)

```
trivy image --scanners vuln --severity CRITICAL tmforumodacanvas/tmf638-service-inventory-api:1.0.0
```

```
tmforumodacanvas/tmf638-service-inventory-api:1.0.0 (debian 12.8)

Total: 230 (CRITICAL: 230)

┌─────────────────────────────┬────────────────┬──────────┬──────────────┬──────────────────────────────┬───────────────────────────────┬──────────────────────────────────────────────────────────────┐
│           Library           │ Vulnerability  │ Severity │    Status    │      Installed Version       │         Fixed Version         │                            Title                             │
├─────────────────────────────┼────────────────┼──────────┼──────────────┼──────────────────────────────┼───────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ imagemagick                 │ CVE-2025-53014 │ CRITICAL │ fixed        │ 8:6.9.11.60+dfsg-1.6+deb12u2 │ 8:6.9.11.60+dfsg-1.6+deb12u4  │ ImageMagick: ImageMagick Heap Buffer Overflow                │
│                             │                │          │              │                              │                               │ https://avd.aquasec.com/nvd/cve-2025-53014                   │
│                             ├────────────────┤          │              │                              │                               ├──────────────────────────────────────────────────────────────┤
│                             │ CVE-2025-53101 │          │              │                              │                               │ ImageMagick: ImageMagick Stack Buffer Overflow               │
   ...
├─────────────────────────────┤                │          │              │                              ├───────────────────────────────┤                                                              │
│ zlib1g-dev                  │                │          │              │                              │                               │                                                              │
│                             │                │          │              │                              │                               │                                                              │
│                             │                │          │              │                              │                               │                                                              │
└─────────────────────────────┴────────────────┴──────────┴──────────────┴──────────────────────────────┴───────────────────────────────┴──────────────────────────────────────────────────────────────┘

Node.js (node-pkg)

Total: 10 (CRITICAL: 10)

┌────────────────────────────────┬────────────────┬──────────┬────────┬───────────────────┬─────────────────────┬──────────────────────────────────────────────────────────────┐
│            Library             │ Vulnerability  │ Severity │ Status │ Installed Version │    Fixed Version    │                            Title                             │
├────────────────────────────────┼────────────────┼──────────┼────────┼───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ fast-xml-parser (package.json) │ CVE-2026-25896 │ CRITICAL │ fixed  │ 4.5.1             │ 5.3.5, 4.5.4        │ fast-xml-parser: fast-xml-parser: Cross-Site Scripting (XSS) │
│                                │                │          │        │                   │                     │ due to improper DOCTYPE entity handling                      │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2026-25896                   │
├────────────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ form-data (package.json)       │ CVE-2025-7783  │          │        │ 2.3.3             │ 2.5.4, 3.0.4, 4.0.4 │ form-data: Unsafe random function in form-data               │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2025-7783                    │
│                                │                │          │        ├───────────────────┤                     │                                                              │
│                                │                │          │        │ 2.5.2             │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        ├───────────────────┤                     │                                                              │
│                                │                │          │        │ 4.0.1             │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
├────────────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ mysql2 (package.json)          │ CVE-2024-21508 │          │        │ 2.3.3             │ 3.9.4               │ mysql2: Remote Code Execution                                │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21508                   │
│                                ├────────────────┤          │        │                   ├─────────────────────┼──────────────────────────────────────────────────────────────┤
│                                │ CVE-2024-21511 │          │        │                   │ 3.9.7               │ mysql2: Arbitrary Code Injection due to improper             │
│                                │                │          │        │                   │                     │ sanitization of the timezone parameter...                    │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21511                   │
├────────────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼──────────────────────────────────────────────────────────────┤
│ tar (package.json)             │ CVE-2026-59873 │          │        │ 6.2.1             │ 7.5.19              │ tar: node-tar: Denial of Service via crafted gzip bomb       │
│                                │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2026-59873                   │
│                                │                │          │        ├───────────────────┤                     │                                                              │
│                                │                │          │        │ 7.4.3             │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
│                                │                │          │        │                   │                     │                                                              │
└────────────────────────────────┴────────────────┴──────────┴────────┴───────────────────┴─────────────────────┴──────────────────────────────────────────────────────────────┘
```

So, we have 230 critical CVEs in the image + 10 critical in Node.JS

 

## CVEs in new docker image

Current sources downloaded from 

https://www.tmforum.org/open-digital-architecture/open-apis/service-inventory-management-api-TMF638/v5.0

The sources are no longer part of the download package. Instead of a docker compose file references Docker Images.
The change was described here:

https://projects.tmforum.org/wiki/display/API/TM+Forum+Open+API+Conformance+Testing+and+Validation+Instructions+Page?_gl=1*54nltg*_gcl_au*ODE2Mjk5OTQzLjE3NzkyNzU5MzQuLS4tLjE3ODUzMTM3OTUuNzMzOTA4MDgzLjE3ODUzMTM3OTYuMTc4NTMxMzc5NQ..

The Docker image used is tmforumorg/tmf638-v5.0.0-ri:1.0.1

```
trivy image --scanners vuln --severity CRITICAL tmforumorg/tmf638-v5.0.0-ri:1.0.1
```

```
...
tmforumorg/tmf638-v5.0.0-ri:1.0.1 (alpine 3.15.4)

Total: 1 (CRITICAL: 1)

┌─────────┬────────────────┬──────────┬────────┬───────────────────┬───────────────┬─────────────────────────────────────────────────────────────┐
│ Library │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version │                            Title                            │
├─────────┼────────────────┼──────────┼────────┼───────────────────┼───────────────┼─────────────────────────────────────────────────────────────┤
│ zlib    │ CVE-2022-37434 │ CRITICAL │ fixed  │ 1.2.12-r0         │ 1.2.12-r2     │ zlib: heap-based buffer over-read and overflow in inflate() │
│         │                │          │        │                   │               │ in inflate.c via a...                                       │
│         │                │          │        │                   │               │ https://avd.aquasec.com/nvd/cve-2022-37434                  │
└─────────┴────────────────┴──────────┴────────┴───────────────────┴───────────────┴─────────────────────────────────────────────────────────────┘

Node.js (node-pkg)

Total: 4 (CRITICAL: 4)

┌──────────────────────────┬────────────────┬──────────┬────────┬───────────────────┬─────────────────────┬────────────────────────────────────────────────────────┐
│         Library          │ Vulnerability  │ Severity │ Status │ Installed Version │    Fixed Version    │                         Title                          │
├──────────────────────────┼────────────────┼──────────┼────────┼───────────────────┼─────────────────────┼────────────────────────────────────────────────────────┤
│ form-data (package.json) │ CVE-2025-7783  │ CRITICAL │ fixed  │ 2.3.3             │ 2.5.4, 3.0.4, 4.0.4 │ form-data: Unsafe random function in form-data         │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2025-7783              │
├──────────────────────────┼────────────────┤          │        │                   ├─────────────────────┼────────────────────────────────────────────────────────┤
│ mysql2 (package.json)    │ CVE-2024-21508 │          │        │                   │ 3.9.4               │ mysql2: Remote Code Execution                          │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21508             │
│                          ├────────────────┤          │        │                   ├─────────────────────┼────────────────────────────────────────────────────────┤
│                          │ CVE-2024-21511 │          │        │                   │ 3.9.7               │ mysql2: Arbitrary Code Injection due to improper       │
│                          │                │          │        │                   │                     │ sanitization of the timezone parameter...              │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2024-21511             │
├──────────────────────────┼────────────────┤          │        ├───────────────────┼─────────────────────┼────────────────────────────────────────────────────────┤
│ tar (package.json)       │ CVE-2026-59873 │          │        │ 6.1.11            │ 7.5.19              │ tar: node-tar: Denial of Service via crafted gzip bomb │
│                          │                │          │        │                   │                     │ https://avd.aquasec.com/nvd/cve-2026-59873             │
└──────────────────────────┴────────────────┴──────────┴────────┴───────────────────┴─────────────────────┴────────────────────────────────────────────────────────┘
```


So, the new image only contains 1 CVE in the image and 4 in Node.JS, which is much better then the currently used version.


