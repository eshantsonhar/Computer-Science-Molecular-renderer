# Offline structure-naming resources

The deployment build downloads these unmodified, version-pinned JARs and
verifies their SHA-256 checksums before including them in the Python functions.
The application does not download naming resources at request time.

- **Orthonym 1.1.0** is MIT-licensed. Its installed package includes its
  `LICENSE` and `NOTICE`; see
  [Orthonym v1.1.0](https://github.com/Steinbeck-Lab/Orthonym/tree/v1.1.0).
- **OPSIN CLI 2.9.0** (`opsin-cli-2.9.0-jar-with-dependencies.jar`) is
  MIT-licensed, SHA-256
  `c2e29326c281f87b59a05d934d8589adac6e9d17b95b984931b3e739111b360f`.
  Its shaded third-party licenses and notices are in the JAR and are identified
  by the [OPSIN 2.9.0 release](https://github.com/dan2097/opsin/releases/tag/2.9.0).
- **centres CLI 1.2.1** (`centres-cli-1.2.1.jar`) is SHA-256
  `6c5d5cafa9393ed7b667a2340222348cd15a9bbdd0d1b92518229f26cc5e87fb`.
  The centres component is BSD-2-Clause, Copyright (c) 2020 John Mayfield.
  The shaded JAR also contains CDK 2.9 (LGPL-2.1-or-later), vecmath 1.5.2
  (GPL-2.0-only with the Classpath Exception), and Beam 1.3.5 (BSD-2-Clause).
  See the [centres 1.2.1 source](https://github.com/SiMolecule/centres/tree/1.2.1)
  and Orthonym's detailed [third-party notice](https://github.com/Steinbeck-Lab/Orthonym/blob/v1.1.0/NOTICE).

The centres BSD-2-Clause conditions are reproduced here:

```text
Copyright (c) 2020, John Mayfield

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

The [GNU LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html),
[GNU GPL 2.0](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html), and
[Classpath Exception](https://www.gnu.org/software/classpath/license.html)
terms apply to the respective shaded components as noted above.
