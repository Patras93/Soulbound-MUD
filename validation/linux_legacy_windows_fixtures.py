# -*- coding: utf-8 -*-
"""Offline fixtures for historical Windows BAT validation on Linux ONLY.

The Linux release ZIP contains zero *.bat files. PREDEPLOY constructs these
legacy test samples inside an OS TEMP tree, never in the user's installation.
Content is from the prior multi-platform release, included as immutable
fixtures solely to keep original Windows regression assertions testable.
"""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import zlib

_FIXTURE_DATA = (
    'c-rlIU6-oJmhFG3*Xr&em}VDujPoF*ASkBt5g;!$1WZ&w+36?VasT_BD?r7}+`H;jb#>S2;e#XhRz4zDtTpFcD^~p9pSlCb'
    '?GE+8HGZ`>`z+k-*YSUZv)xbs=ckFrRx|CFBou@EWl|KuQqJaDc8-<q((pTJ^dgH>?^Fbu+M0RN-tSLO=F9YGs#0s(mfvDg'
    'DnreBi$vit6Wx8(PnWuqjFe?J3B1uJEM?zfhGVC_#7!l|X^mzRTNX{HD-M_VO*O_|%3f{PO}tc9oSrmvgjjY`cmFckB)Z0)'
    'X8t4@ih5!ut-)Z@8bl&%g_^XQddI}_I*Vz3$}E4;3cSvl#u$}yZ|0Ax?=`la`dJqA*i)pb`$)_VA)Yhyrb*y0il{wF^d)mG'
    'SC|;=xYV^#sw)ycdd7Ne<SOn`f9dRFyvtlY<!1eUT`?vevvjA`VXQZO8auru>~{_@Ry~sg)?197G#guP=f!DRhLc88>|6QJ'
    'N$9$4DlQJXIy%JOX&JWJK2W+lT~mcvlXg?z>P*|kern5$S=$oG{_|X2&GKF{U&=F^b(4X%J49Nx&^2Q*U#H2;mfu6s5(f6u'
    'NXfHY*E)w-`Lvd|=dIZ{zukO)=Qy|ZWYBF5blk_s*E7tCJ9)<6a_a4bS?(tI+loDPJM#-+mPu#ayPf8e5attF`@OCjhxwY`'
    '!@lVlW9ZA<z_(~F$Ei1ZCLiJJ+LsrxKgzzl#{D!II%YET%tX(#U8G4R=5wC==6^=*>^#i*JsVSz$!F>NeVntBuWu$5VICax'
    'mnR9ncpkp=%7HCsVSkkAFTFxvc7G1nY^%TMKO3vwoxP&9afskIcou%|UF-qdba!Ui-Np9rx20iksyGm(R#<j1cWFQK*a~wl'
    '-~-3GZ*4;H>F+bg%Xoa3V&dnZ-#z}udL!1|Z`B&chZs2Wnq$rLESnyyb*wP}ajo`V5$|(PSOlWFpWE`}@;<YCI+;s(8+&>Z'
    '=2AOq7oA~pjWgeKJBEF3l{&t=*b=cU%yZ0ZRlx5%Mc|nuWj)Hs*O`z3Pqvcb!B#op6B7gPn9=>OYx28dafv~CPd&z0_-7H}'
    'S+k{_hVA$eYMl;z82AwbCpKHe=Mv+7o_fN2h<L>R-{U@8gj)8Dm_0;G#NN8{>l!m)_nU7UEDnGPLj!jC>EC|py3VWZbS>vs'
    'Z`f6WA3`&qnsz!&MRlw9*na96+rVW{vBoM$Tbqf6P_MqXvQSeyfoG|6gju*A6)^K)D$+0}*QM2y4{((M23Lt>+WJR`Gn^KC'
    'owTH$?RNTOpS6Nz>k0Q?!(v)?morZ|hHayz_eY)RyyNal5F0DWQP<#p^nKY81K;2<?Tgty$bU)3t5!02F}J3p7l49oB)W-d'
    'rypRKQ`0^KT;u){?*Xg?S*UbRaR2XxXnW>$XerOW$f5NdYbrvl3Qzn-|KEn)ru!m%yPE>b*on2pAzc2E=N0R)Z6P#^3}G^;'
    'o_Vpgp}GPy*-I<CpNG4ItI&Gy>%WOZknfKG8JlD#o))o~odN%gDc~M-u$zgXzVc~6p+Ghp=N$p>CdkLyNeE45TWrJ}b&@H`'
    'KmKv=a?^*;{SWwD>~#v*rUlyAHmL#9B~_LwXfJEcG-<CZf<O}FEw_$lKL*rWhqyg@o5BuZ8~6K0YX~3JmolI@+ed8+FmxQ;'
    'J#SU{Uv1ZmFMI)u7bvV{Ne_MnU&C|1HQ*1_Z*=s2u?W2#e8Jp*fVx3t_wHf3>}GDt9Oj-}W3nN?le@~m9sla|tnS0-{sNzC'
    '(6aS5CERGUqu;*xjagB(Ccs9ZtKW}z|Lk)szpH8Z;saxw-AN7ucCRS+=_~4e$C|c*d(R)~7XEpJ|DOZ9k~a6$TH~tX61D0h'
    'pxltsov!)%66n3*X!>=+1JAIwp*X_mTVHt2e~H-taGeDYw0t+skaQUMj?q2p{WC4uO=Fc<f+K+PwD<3l1;K$;4nZH@;+-I-'
    '^oGEr)q6VWtCplM^`suZJ7GrOVu*gflbdvXW5q+8#N`MHlmO8=60llXxVGM|j0OREK`mWr?Fi8V{#;6uRNHDX*SL=14qf2k'
    '-Ayg>x!vvhnON~}loUkk0^SiX!o0WFdq`F^5_1I*h^^rn?+{i%HfbFr84B|>K_a@J!)tW9&X$1?){&CEF#qLq!Z^7Tp?zZI'
    '7zqdv4u5+|&^8vYOW2Fm_67^TRERaUdM~~4@OAp@=+)~Pzj{5(HuS#;u`UShv?Pj_3u>*96dnRvPiBlAVUqnXMzRm%0kdd}'
    '?ab4+lnA|+@^S26zuUW1j8GPQykNq0oNZ6Oo&G1SJraS<RFsfRW!u1B9Eb2__{iIIowWkr+zjka8MWmtC05gAw9-p6VMs7o'
    '%51l#nn=pWKrO`)*sG<;wLPDbNh*z*I&$4qoeUNE)nb9_E@jn2{4!>#xK?(N=u8;ar!-eac{~jmjq7wA<{hx6yEQ~UzV(1?'
    '#o2v&)R(vQ9U@-!wOqnKvIstfxF$PQYErY1Sh?`$|JKBj7fO(nwZ4jLQZV<5MOeWH3ncxAXgx_HS|{yPOqVA<Hof1KZr^n#'
    'i0#dw^07sf$D(&u<AJlK!b~<T7pqVdjx+C+4f@@El(R*kN=wW=i^`<Hx}ISp`08S5z}|W(Ghnbs#iogSOx%{loSuQT?DTZC'
    'j+Z48QN)-lSoVZ<5w9JU)*W#>wcHV~o%Qsd>gYW~W=fZQV-5QhG_E1W02bN>_HkW}FDeF5bet<zUA~?!`G^91!J0;WBMUTk'
    '1a@`w<i@xGY!ytvxV6fkq$k;W*(7m0+f6;-Ak@8kvFVGsM~o$5pDj7Iw@1%&`-&G1u-9eGl+2}GD?hnn$O)L3zvqG%BjCTq'
    '-18S%$Es%4$p;mv#vLfYci7IhTuXI(r?Ka3z_j(VN*5T=O+qSEd822-a!Q)PNf{LY2KF^GxmSjQB{P*dP=<e5>?un#8QPnj'
    'u8j_X2FyCcz7-$y@0BH(F@=3FX4nIE?||<nc#rDh`BY#7$1!jbOM!uh*f&<V7V&rL0E_mp^9Gy)C2kZP_tguRHh5Aq%9&@a'
    '1N({IHVB}Az_V|@7zlBnl>w99fU%d@1%F|E>mqA(EUqy$)6_GMm!$FCdUOaI{}0>d;D((>rZg~N)@OL;vGF@)50mEqg()xx'
    '8YqkIo`bk-j03j7GlL@3+{;{!6u+UCEgSRTF|FhQp4UQ_njM3ja9F-R$HR9PeK*+*l-$aIPwC8y@$SinV}p`D6RrUFHe+wG'
    'h{Ou>@poaaTydbJz(o9xtSHu!q~-!X7GV1!0`Cr#xCFL?o7A&jjk$hi^$CDuSRc}T?-=_YA8><?xv0BoZY^GOeouutN^&w^'
    '^wwb2JDRIWG1T<6QKru`r6WX|1x|7|)13H!Th!w&p(%wZe@bx82EKot-{3aq6?_igSN8)~q1#ToP_(jvv#I8%1&2@r)~y8C'
    'Qfdv$_|*|&)yK!pMgz-^>gz~zK?`cGG`8b3@a1jTPS>x5IrV(WC%}ni@FIMRL}@>y@p{&Ipe(9qBa_2i_p$QJ+7+SpH3M3+'
    'llnp<_U-6kh^GZI%{N?oh8ArN^WqF1S`()Ro|^h?E1UNx8)N~%ZVNmUNk+TU9<W)_Tm#~j!DU=Z2ben97(BCu?SQQa{Iv@#'
    'cFTI6%@2G{|8%d)i?MM(dkaLh71-4?C<C!wL1sO7H(GUfm<#*e&lE?O0(J)OA>E4aiNAXio`txBz6OpXUeaM6BkM`l`2Q*P'
    'GUD(z%F3aW&zL*NXL@YTzxp61mc;iXWJi-dX=?J_%73^Gv+CY%akrk;z2(%)kPXQ;)(SB$Agds3*EdFsYvbLNvM1ka&yev0'
    'mw{hgQ%{hY^(-cvj*upp$ARWj*#&DkX}qV39jT77dYo2hw2LBA;+U_y4;%FZaP+7Z<=HBJ5!`6avis+dkJd3oxdX<lJ3=0c'
    'C-|#QaRxs+iGiK`bMq96MGPDOhNtsfYHTv}65=3TD=6-g7#Ze$?0lRjjn67*t)M4zt~s#ApVqd<Ad3G_YuPszGpdHDhJf6u'
    '2tB6qtaq8Ly)>KX{bGl8*b~0bi7W5dVGr(e9idB=y(RFVzV5>~;h)4E;2A!~8gHN@B=8VBkJ&D+zst!tuh@(0FSZUu#6HF}'
    'SazOges_Jvo66R^v2SF<JOBoqXd`Mx>uv~lx#x(vlU=-AM1is`eC285Ym@f@JMIVSDIJvQevlpag#AW&;^VyN-zazYww*TL'
    'NBVU4#hPE|G|bf_VLEVlgSkUbxtq{aj|1Q~VJ6lFzQB&838AaE)tq^biC9XhGWHhwd_CTfi`Bnhut>h<D5QC29ysuPXOADm'
    '7;TDeN#m~O`L4L%%&TpbC40~A%xYWz&=28jE$ECrRa555;yQoi5T$?PjS7R9bjKgafpC3>_&HtHc^i6Cig{kRv^@hq>MG*4'
    '$K$YZPnt}9GnudM=FQhFItwA}22Nxp@e#0U7kI)F&j)@#CG%y6=Mo{`WK4=Gj`$|i<+?p$;td+C94J}*5&x^ag2uzn9DlV_'
    '7A~v!i^}w8^V~g}6-I(@TAP{O;lKIqQ8CZmn#WT<7QU{&S&UaE?%6as`=5$c2e<((bBuDeO<EkW_#ArK0%KSZFY2Vl+QpLV'
    'T`hYL+YzlRX~sQpp=rZ&fOsGKR1E{JwFBBHN~gpnFGA?w<1EdwAdOY&k;*1t#0Bs-ThBbi(~H2bA9Afibq68)G*4O&WpTSl'
    '=~UI|{)qd-Kmn(hDd#amI7LRuv7&K3*}l7eT}Ir-q;~@`+tbE-eb1Bm(p^_$mY{d3GN^7p^W5!2_YFvIc`d3nKzA8<-suf?'
    'X+^82pG{|47%TZ;I?)l&J|Z#Zu{_L1Z?+qlPP+YqBf51AsRh*{+%>ceG-=>gIV(8z71#@ZERM7RI|m-YPZ#rbywLkmLiqfO'
    'c@D(e9PV(pvi*^&?udyydsaDUvK~USe8>JAUm|XIv(gOJ8ic0WT0pZojZM{^gDliIZoX^3Do$tvb-~BOZBOrCMq8tNf)5@^'
    'pH{KahpwZ10c%&kzi7l+HJ>v5#aw>DXTL{dct$o~14F^NVctt3aRe?d-VqxV56`+1y*GTO_#zIe9@d&67afznEIZ#qTsz?7'
    'w$9$U_e^yi<XGpx5uh7Rz&paM&T5Ld!W_5Yg|F?djTYn!eC{I4!d3Buxj=7W9cR#uuo?1=odB#fT;%0Oxof;P{iGZDvzMJk'
    'piMS>oL^i+SO<LH!pDmk92ja+oAM3lC*;c3ITn%cgWoX!bjsHeennbVbJs&90*BECyp@?H{|(m&ZP=6l7HIkox@3oSAAHwm'
    'e&f@4-!4WzOFlGQk4_=QsVyM?Y<(EV?fs4K_;myO5BQP*TPvhhxt6P%T5^~BPs46suXDqPhB>V{;~WU?r+jEj-}|KF*B0gY'
    '2YMcIl{0ZD_?BzYOCIwFaAgD@E&|Gjz<FW2$aLh})D$&eXDhvLbwX`-pct)o=+ssf|Gy-zYN%F^O`M(-Aa=iqjRs#Roki4_'
    'X*X|EW9RmYAx;4ue#bj`otM;kNEQDWD>#kS`C;}(jTV7dyu~8b1&e}q6KUOJ(ZZS(Z{WbUW)17|`)@RatcTsrZ~L1Nkp3~8'
    '))RavzU@7<uYCLl9ZzdYad$v`9p`rRLtd#rYpQ?pT181?%6RRX_@%M#m%P0iZ}a`)ZSNz%U&K{o4}_25tNesCB=R6tm_a*Z'
    't?sa?)<eXrTo3#KAL9*QJfG<o)CG`5z*^c#uGS7?tMa-X?Q@Vn&T~QFeAdPsd{)r9-{(8X<JN`{^|=;#9wIj2pQKSYpYx*T'
    'wLid6ft{g)4?NF=Zn|-5<9_9XpVm1^=<U)O@bHowf@66OIpljeqn0m9?_*|_v3HLFmHrd55IhtuPc@%$TVI<N;s2lUNRtHQ'
    'sn_?<a;XSuH(N_KgLTC{U-17S_9xf;b(jn9T-WyN+DYG(SRbBkpQ@%iRXWVhU*y6{Lyz}2&;~Mb@kK9JHLGjQ@x<R*U6UX-'
    'b>J)BSITGj<@<MiNn8l<p)K(65cM;znM2X|Hn=^P-#>ie`uLmabjuOe2JV^$q{}@OHoWEH;PrCm%dIi1Y*g(rzz*#oG+B#k'
    '@rV^^3yj8Z7BtkTb-!LRuQPplfA+iX=e03t>Be5cC~o9%{P$a|bvH)4xsL+g6tDj-KGep3oD1N0#9T_84P8U^#j@JFyyb4!'
    'T;@_wD`Tn~WJA$7gl+IUo)M`M)t2_5D0KWb*&{&A(f(iOTw!Zk<w`t1O@8+nCu{sxUhB?_DX{!L7nR%BTH+e~#P>FCW9RR4'
    'gzwiQFZpTTz&j?0^G1!n(ntKd;hIsN4!la=jq~;v|LsvLT3%`@$WQz1Jo`{1s`QUc7+lwjJ8n?bp%IH&k8pL`wtyq)hI3M$'
    'J>BbO>&+4|SKlb6f}}v7r-8`cNC#7HOa9Ai883G^Zk0=WlS_T;JjMHBZ3JC*Uk4q!0<)Cp^SvMP@M`R*%X2R|_@{aY_hqNG'
    'zHqB?S97R8r7VN<fvo}MVZ^iL6#RhkAa7TxR!Dmj$W`DMz%%5J#P2KkJk?zj+V7ir0qsxlJ%!<C-r{)`*8Xo(6aHZ>u3d3<'
    'T_c6o?3E*D`k{XHC+cycg}jikw{Bn-rS{yXzJzS?TFUK!zR&4;YJ%<v91pxs_EEcGp5oY(Xb*ND=NWAIv`5@SJ0zd3^UByk'
    '9GR0;VoqwkIX&9Hlz1P2A+%`D;1|M>$yfK@^`y}C#<{ot!F6{%0sQ*QIyCc54dc$XYgf%&nElnlhpDk`GfSOh)Uz@gTRnH}'
    '!+%ZtE+$AfmGdfJC;vbEKFxU_6HU#D->Q9SC9dqBNyku-8qZ9*hP&4+#4D!cHF1ZvDvYLhbZFjp+yFbBNYmWcWNx)q__cv|'
    'N~^#hQGX0|+HLTB;v#T8LmpxA!v@HQb}_hyuN&F1Z*&Is@f-ChL_%vjZO17%jK+1bQ8A?JR?sl(X@L}w@3;Gc#Opb}@C)TI'
    'Z@wrjz}Ihn8C~jmEnwmERWsI_*W&xEiybuD9yomAPK<E`9-AbCp5)YeZTnGY4prbxpI!9a))rZ({&&5PR$X_`OENH~L-ANQ'
    'cwh0p>iAmL^;q}>^&r45DeXTGwO||jqs>>E?&~=vCGDO4^lv{^-K)QGisjbSrO0ZStIJSh>by@0U`4pMMx8Gkaz+Xz0k-S`'
    'K#FQ%IanguhI1*^Ml%<x>+DDci}+=m#M&ZjYy@wpO%p(t;XaIwovRJY1qr%jhQtm|z6XG>KvqYH7JfZ-qtk|RcssG-RPCd}'
    'U6F`UBMtxv4!E596MmxP*7mF3clcM`<}jS&+W*qcm(9jRqAs}5ThyeckBx~hdfh1aRa@HE=N&lBK%(58=TN0<Q!j72y*12U'
    '+AaRUE&MwE^Y*=*XZrHoQUTa%C5+0HrJQ3vJ6*L@hml18CE+a{RHj~XnR?w)ifeD7k{E9@P~>Xs`(7qq)1g}fr!>B`AnM<3'
    'g}h#0Q-<wIs*@5;WUtm)Kq@lbz2g2qe&*`$)V9W9ucIri^QB3<YWtyf5$X72zo{kntsQ1@|Bl|@uD$Dvb3v6n;q5Q-599Af'
    'Ki@;9&uvibpJ;<>*s-h+IM}<{`|jVbLHO_9avg7u+rKav9XM7<y;h|FF6%%acGh}tG_sVZ1i7|AKoK&j4INB*4IEj<v+zC<'
    '99hcMeoVtr{ASL`YfdtP68Zwy2g-MQMgJ_w-XHvA98@x2(US(CR{?A5)kzbjTaK606ZH|-!EoREM}3=Djg+;hSB%%e$${6%'
    'eJd)a`dS{A-Ji#BII}#S%w<~ZvF>T`@m)VW#CFM3>w|-L&dRVhBRH|}77J1<tZIM1&p{h~(tj85x$D%gdq=<aHNEZ;y7ffs'
    '_oqJ=bn4`fAJS{cju)L|hSRg1-#BLc-`p|HJ^M><(e9zg;T<Ewq1qjkZdLqi^#rQ4Srtfb$5{DUo+cc@s#uLxq;$oR(><E@'
    'J?#EjD*brBlOkr*K&6h7ub%UrERG|@hqD-sjCAs>zf6x<BX`2&F)QVXqcR84o<Lq~38H~y>D-@eAtfw_?-t3X%>wnh^Pw8!'
    'A#9*)F;&d~+p;@>BpH<5^Zdm;B3d%a1b^f7!d;e39bIm!zEOv-n~qe!WhvwXG#4&0G={9N1GJQX^S+A@xPoeuZFmPNGhVE!'
    ')Ad&AQt=Fxx`risraft~H>;;-7y1Hi0r|JdJm+0vyh<?7)#_vd>=c(Ixq$AFYp!4g{#{2+2fsxZ`^$8`4_WXt5THGU1mK;h'
    '{d7w^*4J}cJ?gePzE7^}_H;Qi&8hNlBOSPGBjosiR(wt$j!l10E>)e)w5G@m!GiU9rN2Mx@LiP;yJXf|d`sRM2wiuF=NVOj'
    'H-R_#7m|X1dY%o|yQT-#v%S+HXq$A#jPJHI<Tj6|k8>C=?|=V6ye+@P|2}oIpR#!l`+>DD5_D>J&%;%ZIwyoFA8UM`^If;6'
    '#LLx7^<9`PKQU&Z_b=)LsauaZOl5-)<Dn!Tm@3h82|M<GLKY`(yIAqDiKh;Ax6tXSNI1C`GAj@G)!ebA--gMjv&kiRvp#ha'
    'z=yK)OqFgY3mR+p>1?UXY}ns+dd#z2I$L_X-f!1j`SF}{PwMMEYfL8%yp%amA>h5<^T)OR(OO=gxxT*RduIc^7wa|nb^QA4'
    '^@!KwRM+EF*I#|AD}S8m`d2^E^}pgYS3gdvqcwn*nm$f*Jx+5yPIEm@b3IOTJx+5yPIEm@b3IOTJx+5yPIEm@b3IOTJx+5y'
    'PIEm@b3IOTJx+5yPIEm@b3IOTJx+5yPIEm@b3IOTJx+5yPIEm@b3IOTJx+7|SDfbhfBzqj$#X3'
)

def install_test_fixtures(stage):
    """Create validated non-executable BAT fixtures only in disposable PREDEPLOY stage."""
    stage=Path(stage)
    if not stage.is_dir() or stage.is_symlink():
        raise RuntimeError("Brak bezpiecznego katalogu tymczasowego dla testow")
    records=json.loads(zlib.decompress(base64.b85decode(_FIXTURE_DATA)).decode("ascii"))
    assert len(records)==12
    for name,encoded in records.items():
        if Path(name).name!=name or not name.endswith(".bat"):
            raise RuntimeError("Niebezpieczny plik testowy Windows")
        dest=stage/name
        if dest.exists() or dest.is_symlink():
            raise RuntimeError("Nadpisanie pliku scenariusza testowego")
        content=base64.b64decode(encoded,validate=True)
        dest.write_bytes(content)
        dest.chmod(0o600)  # never executable; Linux-only regression fixture
    return len(records)


def remove_test_fixtures(stage):
    """Delete ONLY our unchanged temporary regression fixtures."""
    stage=Path(stage)
    records=json.loads(zlib.decompress(base64.b85decode(_FIXTURE_DATA)).decode("ascii"))
    for name, encoded in records.items():
        target=stage/name
        if target.is_symlink() or not target.is_file():
            raise RuntimeError('Niekompletny test Windows w stagingu: '+name)
        expected=base64.b64decode(encoded,validate=True)
        if target.read_bytes()!=expected:
            raise RuntimeError('Zmodyfikowany wzorzec BAT w PREDEPLOY: '+name)
        target.unlink()
    if any(stage.glob('*.bat')):
        raise RuntimeError('Staging nie zostal oczyszczony z BAT')
    return len(records)
