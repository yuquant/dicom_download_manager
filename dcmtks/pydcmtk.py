# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 利用dcmtk抓取dicom图像，输出到以A号命名的文件夹

from models.pydcmtk import DcmTrans
if __name__ == '__main__':
    DT = DcmTrans(server_ip='10.0.2.5', server_port='104', aec='SMIT_LOCAL', aet='SIMPLEDICOM', my_port='10000', output_dir='/home/liuweipeng/dumps')
    DT.download_dcms(AccessionNumber='A002207418', SeriesDescription='iDose (4)')

"""
import subprocess
import re
import os


class DcmTrans(object):
    def __init__(self, server_ip, server_port, aec, aet, my_port, output_dir='.'):
        self.server_ip = str(server_ip)
        self.server_port = str(server_port)
        self.aec = str(aec)
        self.aet = str(aet)
        self.port = str(my_port)
        self.od = str(output_dir)

    @staticmethod
    def _if_err(response):
        if response.returncode == 0:
            return response.stdout.decode()
        else:
            raise IOError(response.stdout.decode())

    def get_uid(self, AccessionNumber, SeriesDescription=('', ), QueryRetrieveLevel='SERIES'):
        """
        根据AccessionNumber，SeriesDescription等获取uid
        findscu -S 10.0.2.5 104 -aec SMIT_LOCAL -aet SIMPLEDICOM -k QueryRetrieveLevel=SERIES -k AccessionNumber=P10463706 -k SeriesDescription -k StudyInstanceUID  -k SeriesInstanceUID
        movescu -S 10.0.2.5 104 -aec SMIT_LOCAL -aet SIMPLEDICOM -aem SIMPLEDICOM --port 10000 -od /tmp/A000950892 -k QueryRetrieveLevel=SERIES -k StudyInstanceUID=1.2.840.113564.143313582280.5700.635186415302296489.506 -k SeriesInstanceUID=1.3.46.670589.11.38206.5.0.8996.2013110610015734338
        movescu -S 10.0.2.5 104 -aec SMIT_LOCAL -aet SIMPLEDICOM -aem SIMPLEDICOM --port 10000 -od /tmp/A000950892 -k QueryRetrieveLevel=STUDY -k StudyInstanceUID=1.2.840.113564.143313582280.5700.635186415302296489.506 -k SeriesInstanceUID=1.3.46.670589.11.38206.5.0.8996.2013110610015734338
        findscu -S 192.168.231.18 104 -aec med_imFIR -aet dwtest4 -k QueryRetrieveLevel=SERIES -k AccessionNumber=A000950892 -k SeriesDescription -k StudyInstanceUID  -k SeriesInstanceUID
        findscu -S 192.168.231.18 104 -aec med_imFIR -aet dwtest4 -k QueryRetrieveLevel=SERIES -k AccessionNumber=A001873983 -k SeriesDescription -k StudyInstanceUID  -k SeriesInstanceUID
        movescu -S 192.168.231.18 104 -aec med_imFIR -aet dwtest4 -aem dwtest4 --port 10000 -od tmp/ -k QueryRetrieveLevel=STUDY -k StudyInstanceUID=1.2.840.113564.143313591524.3208.636225732687445043.183
        判断逻辑：如果序列描述为空，匹配study uid，如果有序列描述，匹配所有

        :param AccessionNumber:
        :param PatientID:
        :param SeriesDescription:
        :param QueryRetrieveLevel:
        :return: PatientID, StudyInstanceUID, SeriesInstanceUID, SeriesDescription
        """
        # TODO 存在多个序列名称相同的情况，会报错
        cmd = 'findscu -S {server_ip} {server_port} -aec {aec} -aet {aet} -k QueryRetrieveLevel={QueryRetrieveLevel} \
            -k AccessionNumber={AccessionNumber} -k SeriesDescription -k StudyInstanceUID  \
            -k SeriesInstanceUID --timeout 300'.format(
            server_ip=self.server_ip, server_port=self.server_port, aec=self.aec, aet=self.aet, my_port=self.port,
            QueryRetrieveLevel=QueryRetrieveLevel, AccessionNumber=AccessionNumber,
            )
        print(cmd)
        response = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        res = self._if_err(response)
        try:
            study_uid = re.findall(': \(0020,000d\) UI \[(.*?)\]', res)[0].strip()  # 先查看是否有study uid
        except IndexError:
            raise RuntimeError('StudyInstanceUID not found,', res)
        if SeriesDescription == ('',):
            res = {'SeriesDescription': '',
                   'StudyInstanceUID': study_uid.strip('\x00'),
                   'SeriesInstanceUID': '',
                   }
        else:
            raw_match = [re.findall(
                ': \(0008,103e\) LO \[(.*?)\][\s\S]*: \(0020,000d\) UI \[(.*?)\][\s\S]*: \(0020,000e\) UI \[(.*?)\]',
                x) for x in re.split('-{10,}', res)]
            info_groups = [x[0] for x in raw_match if len(x) > 0]
            target_list = [val for val in info_groups if val[0].strip() in SeriesDescription]
            # docker中匹配字符为'1.2.840.113564.143313582280.5700.635186415302296489.506\x00'，将会引起错误，所以加.strip('\x00')

            if len(target_list) >= 1:
                target = target_list[0]
            else:
                raise ValueError('{0}: Target series not found {1}'.format(AccessionNumber, SeriesDescription))
            res = {'SeriesDescription': target[0].strip(),
                   'StudyInstanceUID': target[1].strip('\x00'),
                   'SeriesInstanceUID': target[2].strip('\x00'),
                   }
        return res

    def download_dcms(self, AccessionNumber, SeriesDescription=None):
        """
        下载dicom图像到指定路径，不同病例以AccessionNumber为文件夹命名
        :param AccessionNumber: str
        :param PatientID: str 选填，多数不必填
        :param SeriesDescription: str,所有可能的序列描述列表,用逗号隔开
        :return: dict, PatientID, StudyInstanceUID, SeriesInstanceUID, SeriesDescription
        """
        safe = re.match('^[a-zA-Z0-9]+$', AccessionNumber.strip())
        # print(not safe)
        if not safe:
            raise ValueError('Illegal AccessionNumber: '+AccessionNumber)
        else:
            AccessionNumber = safe.group()
            if isinstance(SeriesDescription, str):
                series_desc = tuple(SeriesDescription.split(','))
            elif not SeriesDescription:
                series_desc = ('',)
            else:
                raise TypeError('Expected str in SeriesDescription,but {} were given'.format(type(SeriesDescription)))
            meta = self.get_uid(AccessionNumber, series_desc, 'SERIES')
            StudyInstanceUID = meta['StudyInstanceUID']
            SeriesInstanceUID = meta['SeriesInstanceUID']
            output_dir = os.path.join(self.od, AccessionNumber)

            if series_desc[0] == '':
                QueryRetrieveLevel = 'STUDY'
                cmd = """movescu -S {server_ip} {server_port} -aec {aec} -aet {aet} -aem {aet} --port {my_port} \
                    -od '{output_dir}' -k QueryRetrieveLevel={QueryRetrieveLevel} -k StudyInstanceUID={StudyInstanceUID} \
                      --timeout 300""".format(
                      server_ip=self.server_ip,
                      server_port=self.server_port,
                      aec=self.aec, aet=self.aet,
                      my_port=self.port,
                      output_dir=output_dir,
                      QueryRetrieveLevel=QueryRetrieveLevel,
                      StudyInstanceUID=StudyInstanceUID,
                                              )

            else:
                QueryRetrieveLevel = 'SERIES'
                cmd = """movescu -S {server_ip} {server_port} -aec {aec} -aet {aet} -aem {aet} --port {my_port} \
                    -od '{output_dir}' -k QueryRetrieveLevel={QueryRetrieveLevel} -k StudyInstanceUID={StudyInstanceUID} \
                    -k SeriesInstanceUID={SeriesInstanceUID}  --timeout 300""".format(
                      server_ip=self.server_ip,
                      server_port=self.server_port,
                      aec=self.aec, aet=self.aet,
                      my_port=self.port,
                      output_dir=output_dir,
                      QueryRetrieveLevel=QueryRetrieveLevel,
                      StudyInstanceUID=StudyInstanceUID,
                      SeriesInstanceUID=SeriesInstanceUID,
                )

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            else:
                print(output_dir, 'Dir exist')

            response = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            self._if_err(response)

            # p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # (output, err) = p.communicate()
            # if output != b'':
            #     raise ValueError(output.decode())
            # 返回字典或者列表可以任意增加返回的内容，而不会影响其他程序的调用，字典有解释说明的作用，如传入参数可以涵盖输出值，则采用列表。
            res = {'StudyInstanceUID': StudyInstanceUID, 'SeriesInstanceUID': SeriesInstanceUID,
                   'SeriesDescription': meta['SeriesDescription']}
            return res

    def move(self, AccessionNumber, aem, SeriesDescription=None):
        """
        给一个pacs下达指令传输dicom到另一个pacs服务器
        :param AccessionNumber:
        :param aem: 目标服务器的AETITLE
        :param SeriesDescription: 序列描述
        :return:
        """
        safe = re.match('^[a-zA-Z0-9]+$', AccessionNumber.strip())
        if not safe:
            raise ValueError('Illegal AccessionNumber: '+AccessionNumber)
        else:
            AccessionNumber = safe.group()
            if isinstance(SeriesDescription, str):
                series_desc = tuple(SeriesDescription.split(','))
            elif not SeriesDescription:
                series_desc = ('',)
            else:
                raise TypeError('Expected str in SeriesDescription,but {} were given'.format(type(SeriesDescription)))
            meta = self.get_uid(AccessionNumber, series_desc, 'SERIES')
            StudyInstanceUID = meta['StudyInstanceUID']
            SeriesInstanceUID = meta['SeriesInstanceUID']
            if series_desc[0] == '':
                QueryRetrieveLevel = 'STUDY'
                cmd = """movescu -S {server_ip} {server_port} -aec {aec} -aet {aet} -aem {aem} \
                    -k QueryRetrieveLevel={QueryRetrieveLevel} -k StudyInstanceUID={StudyInstanceUID} \
                      --timeout 300""".format(
                    server_ip=self.server_ip,
                    server_port=self.server_port,
                    aec=self.aec, aet=self.aet,
                    aem=aem,
                    QueryRetrieveLevel=QueryRetrieveLevel,
                    StudyInstanceUID=StudyInstanceUID,
                )

            else:
                QueryRetrieveLevel = 'SERIES'
                cmd = """movescu -S {server_ip} {server_port} -aec {aec} -aet {aet} -aem {aem} \
                    -k QueryRetrieveLevel={QueryRetrieveLevel} -k StudyInstanceUID={StudyInstanceUID} \
                    -k SeriesInstanceUID={SeriesInstanceUID}  --timeout 300""".format(
                    server_ip=self.server_ip,
                    server_port=self.server_port,
                    aec=self.aec, aet=self.aet, aem=aem,
                    QueryRetrieveLevel=QueryRetrieveLevel,
                    StudyInstanceUID=StudyInstanceUID,
                    SeriesInstanceUID=SeriesInstanceUID,
                )

            subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)