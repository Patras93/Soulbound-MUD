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
    'c-rlITa&U_lkR`%+n(70SiaLt#9Rm^2r8wV<)%YGQ32&Gk2taa`+jnPidDXcuY31Qe_wb}QB}%etvo#WWUkEr{-x8moz6fD9Q}7|'
    'v(LiKejWdxaJu{DKYtmk?rN(3mV`o(zmAI{SW4MU&CaphS?Yc}jb0^T;+={>Rk*1q?)~26G<=;Lhl<EeTGBig#4=RPc_i?Mso?CR'
    'Ub@ue#E_SrB=C$)SW3R>>b8}36DJjAn=__kOA>~5M;I*eouZGt)P1uYC-G86w!7lM=3~iDo&D>0lW3~@GWEyFK+uw5!u9)Ot{(|5'
    '7pmfF;vEyyYcD4GDKq^A7kKS6tuZR4?$kG`&sBFj@v|)Gx-XHc>?0vNgm})>n<Rn1D5BOl(Uz`bI{a97k4sH8QcV`|qh)T_H5}Pl'
    'YOn2mjCT!JFZr;3zb5Nr&owohYrAfD@-ni!OUUmWV69pv1#WjSveRs2I_+1RGj%(S#Mn3Uft}EG*+f_zG{rc?-f0=O+<hQ-cABd2'
    'u`2E+zS*9%iv7fr7Soo=ll*77vYO`IWVV#1mfK1C>h2J!*+NtG#cZ7>Q%iae1(WYvFNU0Fxu&)cvHVGwx96?huYRlf{`PTZX-U7s'
    '^)=kb*4NdCV`uyYzsrfY<EOck;5Qe0%694({4^8KxOY3rMLx{Or2D<5=!e;w-s67Nu*T4rwt;WbUXByb_(C?q^xBgav2SGG)NwCO'
    '2KF!+c*8`?vt6W$CH8Zk`NRK+TG@G!vwJo}St6UI&-ZcemQ25yScG|S&|Y6e*y4Hc+AaH*l!ZMb(_XuUw(R^GuHCKns{N|3x_9!5'
    '*7_lW-QZdHzI%}eWYgIV%g!#geqNTkwW<6-5V^4IVDI97>bWcIxquBEXTG@!g_pn29xv<h9rB4^gI?$O1AW8Sov)P+<3kJ_dCQ^m'
    'Jj*7>N{=-Lz^|3=8~lCd@ryuE_A^TwU*0z?UrxiNw2eJ233IU(wTkv2x%!#!Ic?oKbESsQF0zC#^RpcLS{1PSb`f|(LtYyh*}BVT'
    'z>}@0dyrL5_~Z(Kcg*Piw>8;avAFmky{BH|8|<@)@T}=lO2bxs2-S8QHVpiTffJi8{BwzQf0=mvdkBBT|L<|nU4&}(1wMO-mhioG'
    'W!E)kK<+o&*4;P&CJc1Q<(Gf^rQ_IdmfbP!-@QRc4!#S`Y-{T2FcFlk)^+z2Pu~WP`x2{e1!?PHV#3v{&&@1Um3H8n$_#E6u8jg>'
    '?oR|-#`vmQE%^Xf8DMagh(k;J2ywd2xo=}m>{?E{H}YLBSaL78|LPW#va_6e{4s3loYphi(Rs(rl^`~jlcT1>{OI$tEd;*KVA>b5'
    'eUSf_j8<IIe;sazwpIWNwvpf@Lo59NyDT*AL%=oeFYzA0N|1$e=LGZrmW#HgUYk^T_5}v5=U7$XVwHR1JNkbccADl3_w8&7sIeWZ'
    'i$l2lBhM?=VatST78%^6Up@08Yh7`8cj&%y+5JA8B}|3%y{~^KHbK5`05UeoR5&eSAv**97Zboe!ohATAoP_leR2ho*(h)GcsD^l'
    'bSJ_!UCVS0*H*@vocz~+-J9IxX><PzHWz#C0<z%{Hnz>s0P2#;%M@WR<EE;(*JPe23Np{l<FFS4>diykGUgM=A#CA(U*`s}QEe#!'
    'inD#xG66%!{@wFdmHpLnz1YG7SiC@CO-s74E7%&I`?Udo2>p6n>lKU8+rbuw`wvjpujJl2OqQL@NnP7@PL4j_kljfgx$lgAx4UNN'
    'X>)&p%{9WZIiC=2wA`cLy4cOI3e_qP86jN#Jl_4I&#mmP4#O847+LNe<<KGbD&)RA3cc^pX$!db<zu*oeI8-|=fJ9{&3$OCaaDFG'
    'v}y)WZb0cyXZZFSXx)J^d7SXTGR$o#7+5{`z;gb-ko^zWnXo|9chU?=hmOx&x<|QxrYSjTtWcC-2q3@g{kvp=w;`27(1W#jCy*(v'
    'LGVa>FDGrqiP}<2>h(KgSMQlFyx(u<L%P19@z5f2X&`~(K{^c{+RDPUIlo3U5YP*1X)?DXL<`t+DM?Z+lXD&Yx`sP+frWQAHOXgk'
    'x9Vp?<6kK$h}H$HBVL4gcdvDktf)lh3LucXhGo2iSOM9@b&O;v%+myk=za#P(dar$0z#NaO7_D1x6cXV_>P43C@RNDK!9-g-A#g)'
    'zIa<gUT!UKMB&#8u|{V1wL2QTO@24tysrMc*EKC&`->3kg3vZ6lDAw?YlWon5Rg7yePr|F>|YqkKCB0kMO|#Cp0=e#=&h8FBmer@'
    '-l1ZIykP4^BwWYY_T*dXe~|8x2y7;Th-50;2G-&@fGxvD=96{C1^#f;x7uaYlD3psO_tG0D~E}T1j9{T%i)wElJXHyOSXCU&6K5D'
    'o-fHb6-TaOI8LgJ2eR~Lx`E;>CB=jPx~{3<TFF78Gj^e$a=6mV<Eih`x=zPI-bU1Pwz|O9x9*dySahEpwdGB}1Nf`9mP*)17Qv?A'
    '*CeNkO{yjmD+l)cKbknQLJ5*G?vY;;gSlrc{0cT$An89u>v0m1p43w@S)SP1v|dNNebyesw>SOD#uiZ?3*K3Y`}UR!GufnEtU`f5'
    'PQ6ps?{)T3?k)mFTw?E8R3-)VdWMW(tBa)$d26NQ0)ss&HjSNQ;&7sCcXjBp-PM%ZUzSKj;bRVOT4T2Ze{CzIclhnZbPQm-+ts>?'
    't#x(Dl{;h`Ysjadbq%lvM4??^9oN<RqM{E*$702*!}RHpjmW?k=rro-S)jT{U{_m9ZV@+ttb#EjZq4$?=}9tQH%Z*eb`uXc2zKvW'
    'WcoVX!^e`a=Pntxw~Q|{>xvgPu-9?jp*UP>HS?3I2suV1X79P+g#r9GUFZBD>sZxMb^L(^DsdYO@Ex+VOvhB5?rG%N8${arS)~IE'
    '=p-Q(syyQhVL2tuh)Ee00Q%N7Gr4DmyeYYgYl9j7WxgjbhsnU&>@?Ll1S&A=4Ea{^n0+oU5gAj+2Wy5rAon)n-5Bpt96X;2Y>06#'
    'Vv(By0}rvUuW&8=@6-ks?IGt4Vh)(NUNGEOF0r%`Csn<idgeN?Ug&N801OCmcJ2!SANSlcaK$+=_TsyUU(jz|WQ~r+)rY34a%TRL'
    'G(KA!hp_Q~*c$e4*r{i70~4k_7tcI4zNhSA-29)P0CT{BvgqzP@XN+JAPYP*C_>e_?Bz)Q8>-o|u@C0cavtD$9J18x803V*()BqW'
    'J~QdF@un~5W(Ispr(TSAk2ee(<n#;S3UF^T@)nCos4ySD7sHh!^yL(oi0_dV#cGn&v4E`w*nWr*cl&Z&0^1Rrl(SZ?xqfE#69C7c'
    'AL4!QSo<D7hz%O{qU<KQxp>RjJr(B2$!Ykias5^II9!d3fvT<bGW{}@+kB*&h)K?7l2iQO7WKMIa7sSPUlLrif$d-S*T3y~1)Ia?'
    ')&0O#@V3(~6wIt|Z>s&N!68(Ebt@jS6uChezuA1O`1o-$qi<SKeI0Qwa6#1(M^>B$zO)Tn>H3W@r`|8w1Y%+tyz*ZoLEH~$y`FjQ'
    '%ZuvS$mFoseJuaBb_B3}RR`B>r#|2CeJeWX!fAm_bB=4z;G*0hFV2WVYl^9Xr=)(%%x1mu23Y{G+eDm+M7>pU56G-&>VV=(|FSN*'
    '4NM(xbe7pdcEDCR{@MW+J7vAk<_~O5`*g3uim`Don+Jlz1y=P8%0MiKm)x$iGgh4)_Tv8ZGX>*Pz|IhRh_~W%ir-xk&w}59UjxVC'
    'FX<qUk@X~N{C|qQjAHnlvU2d`Gxm<)GdVW*U;V%*mK5&|WJlvYacZ*N%6^y(v+CYXai`Df-g4q)$c7{fx`L1M$SMfiwT;d(ZoHdN'
    '_T-zbDKdWGGVqIW>M=62uIWlcn@<z$<3M|<<N{re8}F%nN34CUUZ)xAt)htJIA(hHA){V^7;SJ-o~`0n-ig+3cK;l*(b}gdcffiz'
    'o6kex1bfxU&tOL<A+VBvY@d9wh=BvZ@N|}ojYEcRLNQ2F3-Y@pMuvIsJ0JH+>oW_|75GHXI0tn6Nw+lyk^g_vWlvvBsT!i_JaVTZ'
    '^jw8yy~||nrP)~P6+7r*PxwBgSb499Jz}3@^Bt<}ErAF1bsyFV`=r=`IK$Rh;|+L(h&be)NA51JKg-EBuh@(0FR~5<_&(OuU$(zY'
    '{m%M|H<he+BVW%3c>oMJ(LvOT^se)Fxu@Ye<6XR5M1j05eEDVLtK;{+d))VxQ`#@neLp+y3H$Z(#MXJ?zftb&Eh}xlkND~CfzGdc'
    '8sy56FdaC&!QR2AoK5H{$3AeIFcZ3gEx1SGgy7ZNYR@dkgfFF38JmYb)5jdSSpEG4i==CgLY!ynAqJlB<nbLJqeHPRaop7`-xc?V'
    'd9{qPWbaw+X)WvT+97O>1JBq~HDx9*uKPz0QTn&IQDKlP-o+2(K)61G|C}y*-iDr-VxN~-+L|IhY6|?e%lxo$Pnt~pVKQ6Y?VIT>'
    'I`bjqhM4G<6pw&ayTId@cs}s^C7CVTESCt`A!AZhe#8!$F4yhh6LWB|vM*=xNBpny3R;hQX85a~vT#}XUsR^Q4$qzAu);{h8*VeT'
    '+Uz^OWfZgAspELc*247a4~x-ih<i58nEem=stw!#mpMkc(jqPnU;Gk!*#c`=P+ZiAi?xa+<GX719=0OVD{;m>aG@!~a{zxI`BV)9'
    'uC)R>C`u<3OJ4cVzsFhHV?i9N;v<zz9{2_DH(O6V_|q%Tt{*V2LUji|`?OEehrGDmBe$z+bkAV+(3cU@%ap}2oj*l-$*`hvJ;}ba'
    'ep^ON#>966A=}fzdwtK#@U^q9)+~bWQe{xtevWguAG)tke9Pmg)&Sn6<9Vk!<ibU(mtTkWq|jH=VQ5E3Jo|{mnECP`Gv<~P4DEFL'
    'AVzd*A5sdcML2748F13Tsd84t)Hh%+?6Ek~0qhKT1Up^K*6~8?MG4{a8}`{3ZhN@H-AeXHs=C7`?&MkJpvigw&hicUGkl4d+=mrs'
    'sB{nx6>b5}W;YI1cQ&$6{kZw2{3<`81Jngu50gE;e;IA{@&z_{Bz{`?Mi0D>@&)Lwet*&MvuZzO`rB~%AfEjU$ME!Qwg!eG=7xDU'
    'i39_&xOj(ekUxCU<mkO&GsOcxq<R=PMJ_rbep$A^hPbxR)@`1>bN36?b&zA71DgkLI05env)Zc({0e*AA}&0ZyJ{@R7TDeeHw#zA'
    'clH9l1wBr|8zD2~8#^9YsXNHa^>WvEZ~BQhvS%;bi$EQ3*g79vLs$oV-@?X=7%?zZ#TMlo;7`bv&2uau-$#7I{?iH5BkYQ}tm>=>'
    'a)cO02k>S#EZKLshHpWh?7KkKcHkvD=)M0<oB6>{<9)jr`7GJcU~Qa2@>7dP{>gn<$L;-%&)9W+>krrx4_V8^RT-D7np$#)*-t}m'
    'kM-QJp+QbMcUcTX?5BKaOP~A1<JTtT_y>9(a+Nd1P{dotMK5{GAHWp@akvO5A41FvTScZJ-=?Oh**aTkJ+mFEy94=Xbwa0bmH+>i'
    'IEt>AU3YAE#Q?thz&9H4LT)djo<yg4n;JW}R}8TW@bJ61lh=7korhHZkF_GExpjV+&8g8M@QQgXP+hPn=rob^9t$RPQp^zp=gk_{'
    '<@+Brgscah&5!Mk4~YNhHunM>if?BRt!q4<gU6Fj$?p#Euj9;$z8hESpEcD#S*@a^HD#=JP4T6n_e<Vht+)Ap;db^B;5YoLaR$QH'
    '@F+ha4v9QS;iurv(A6C_)qIHJD&qrxz{Xg^7t3dQ1$6;r5wMm{k}KU|ZB<^kqjL_j$63zvES|Nn2j4A7@Avr*^0>9mM?J<xz6{_S'
    'uutNso6mVs^V;uVDDR%ZgAXjv1aG><)W-et2Rp5ElF-|wQ{dqxH$;qOIplzy<rthVi0>oUEMxB;11kQ<XCdNHv^>@EjLG`iv<UnE'
    'j7O@-BTv1)f0~O$NT=Cqvgxm@*z+L%A7X!e&0hyO|IT=Audbc+hN9bpWm~7J=}r+3)ANH|SZ?s~-Ui%2qF8+4%T>+lT5~+HcUIRV'
    '@J$W)iuaY$8Fu;pO<NKcJZxwSJUm3bjB(~r(7*O?&t>-yUKv0BI<z~b0o}k{(|~xnr$C0cTpV$|oca<saw{2CXAF=-D+q@!N40qP'
    'ins+v<2w@^%HZzxC9yiw!~3(Jx}Vj?z@-~!1xDP+;n?>#U+Zl2R`VPMaZ|YdU3{pGeLok#_wc!tVm5dU)fda^?DCeoU2~aBJ*|wX'
    'ZjcQG{SdYg-|>t{5vjJc4+XyMw@4lVe2&il+UE*e(<)bD`DyagYaFlfU3slLFDAh9`&?9NU2BPJ#3y#Paa%ikpUr=}9(l=6dph1R'
    'hMzZT^c6p1*A3P#<>|ny^j$x1Z~oshxM+E)sUSb?x##J}8c``ZQ`Mmy9J$Om34In%8E-~zvxr&aX}b+>cBxY*6=#xGu~5Y~Q@~z*'
    'y_oQ#41S&lg0rvvex-E{!v1~i(|%#wRDZXmT?}lwo&l*M#fld01?Q1CS`XEKn`hsY_f}^a606M(8vem*C9iyarUkCyOLgr7IKlq!'
    'Y*;+avzL3$Z_Yoj-JRd+r4kpd?>SXnS4`m#E5r?MA|!_gHJbH<d*<M%;EWZo=vOtl?d5rcs*e1rPRnWuHYYZG=mEzYCSzX$#}Ea|'
    '58=;zlpDl{_R#Ah%wym`!!34}5<`{|tGBwayY?D<2XT$C%BW-h%V)0LV)iMr^N(eF8wyGql}T-{ZNh)X@$O`yh|M}1^0XLy5;28h'
    'BXofKSWTS#uRdesC@<|(PA!ORZO|9+bh3Msqv8RU7tJ$_y1ul4Zm5=>{Z#GnC;4&cWpuX2;w$)BI%yRY3y7~#qwXPYWi5*T6MLJ~'
    'JT9y1ps;-pv4nL0srHH3wL(r?(ivD#Q0=jb8|miLb=h{^JXiI(6P?}7t8>pdrai;g83sPQSIHc!E55m|slL(mR&=_{bw6BZIig~x'
    '#>nhuZ-@qQLk~?JLF*26{`>tkIuH9jckg_HagB8<UhThxo*JCj7pPB!n!BOfwefXoF%Ed|6Zdfj&pc6w(hqp_9S@>-MzveS39YuD'
    'EdFq=)8Ovu`qFdZ@!ValGVl#P?2WM>m(HILR6m4XSA<=C<=WqoO<FF;`cW+8a6WR(9@87~-g0K8+dhlUMm$iB7Wg4s*F{Faa9lSL'
    'Av@u|HZ37;x9R+%YS=C%-|i~*n9F?AiAQvfY;%U<@Xj}428$)tyXy0$Z^n!JTKHw({p*=U4o=*=_cO%c_5<#IIUj}Z^Bmqw=NK1E'
    'z2}<#Vg>mlUWj(>m#l7Dou_LLYK&KTxGtyk#`Xql$hK4AH{h65&gdN;JEv*(IB_$NU*S9CRlrMJTk(G2rI5iEP6u$qBA|2lZ`X+4'
    'i9_}4evQ7hUB5N@s2VZ(JZXX3sK$omOtGrwSIBpWD`?vwKk<=})V!AQL&CZ_{9-{lntz7<^WvQG#Y~**m)dy`c4S|31-s6#6zWXw'
    'tNa4-dUMTL!SP|I$5`%cY~HAO&FLcsZe8d!zVe>aAn>#L@AR8`xN;V*9%P|<!kuh>Zr=|u`hHKZS|KN_Z>;LB{=t;ht?5vf6d3Cg'
    'BuAMMNmy5e@YYE7uwl%QDM_^?52Uc5DW`$V4h9g|;ka_u2vLDscBFz@{EC2}F0w|W!iL(2HEbC7VQucYI#6Fw!jVit5CB+vjX6UG'
    '<y6<xv;;Lggtv(zyJ~Od?~0f%HHv{SL#WG%KV}n8x3+ZUegdVMhJfH~$NHyk4sJHiQpp<havn90(?2%OzG`(N>!Y^G$MZOh0s#{5'
    '=8Y8b+H}sE!fy@Tmv*4aG~Y&lUcQ%kyN7di1wtX0xKu_jr5yX&X^N@XE>Yy)64r7=$0$pdMqQ6Q<JwxNWXsxMWT|S+xKCrQ>H4j~'
    '7_{TsBCCC~Rrh-RBU*9hYf7R0iJ8E^Q(GkqJ#9_q&X*yAik?wBlX(2T-E1zQ?$WNcxPM3YZ`XeKU~Y}I(dw){OZu+=)%Sk~nLfAa'
    'x&J_$UPF#$J%D5FrtiCdzdGT+d&_maId1<#XS88hA@u^5d<h}!S+3PJ3{!qdVqfP8C_-0k`7M*q&0)wAp2c#ujOt7b-W!JEH)|TK'
    'CMv-x%>`W_$lvT`{<9!^KbY(?P|1859P9?@mBU(EH3=nm%F%LiqCWT98SZ;isjs-j95Jh6czsSo2D}c4?^7tI`fnbVonJ>VxM6ub'
    '4Z$~Rj(_TZeAjn}EH8DGda(7*SY7DGfD!Zam>0RQs!ji#fj0X1|1RKjH%U_WHb1sC?aBc!J^R}Ibkc&RqW<_0X@hpWYD6>au4VsV'
    '4E}$(qn}y!Lu*m*p~q&KJb$Q8uf^Lb)3v(iB+c$UR-LNHtl6wt6OJHNXk!)09l@|W$Dwr(yMH#6e!SmK;j?L=P$lNkb4;oVD6wV1'
    'v&R`_?(|HDA;gDSA=~EN;W!oXOfdS_$q_no#;!DSOKEH?t_^QbKrglg(Ll0v=8w0a5~j^gGo_*B2FmqhPSHmL$UswLs_Fu^C1(su'
    '(l0yb+3WBKZ^`I%><7~|jWwBb>Ns>#Wloh6Cp8qGGi9;?+6$u?s*9|nP1Ud;-gmJ9hgXIq8`dH1>aS+iiG8cYDtLxMUF{-0(;9Q`'
    '-0W)EC43=l0r|JdEN5Me_}igQvubh%a*9i$TtIiwHHS9?|E`)ymA2?2e~IQ#ky(AAYUu<NfOSgu(k*pVT;~S6)D3uiA7AzMavAAo'
    'q4IA-9T;sR<oJMAY)>D?`oBe&s?K}TX%SHrtmo<e{!xdW`h7UXHRtgyd21kaJ-v`;bV{)ayzxH~75vltY(%|ldQd&vI~{`7kY*s+'
    'X<&nHGk^NHhtcx>`|tSM@*)2BXxieG&8P~DsC}WJ6RUF`th&_M!%x^+<MWK23cn;Cop@9y82ohkDPk5{@4`Nix^-RKRowoE^-vN|'
    '6=!-bVaNVY(Bi~t6)Uzj;nb$?E2>IG{K+wqS$V*(W=8>iH%LCs&X<Ur^;8s9`?B*?5pR<(4c&d3eRf<6^0(}+>zNMCKHskQTXn4b'
    'IEUXAds^3I6-+O6ZLko;z3!Kfy8fOnug_dx-|?;4Rqxe&3w|HH{eB%md`=xcrw;$>sl)s^arn<ZariGWZP<%b>bMTrDduz9@HuVx'
    'oHl$;8$PEEpVNlVX~XBV;d9#XIc@lyHhfMSKBo<z(}vG!!{@Z&bK3AZZTOrvd`=rarwyOehR<ok=d|H-+VDAT_?$L;P8&X_4WHA7'
    '&uPQwwBf(_wBi5#e^0(UX#'
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
