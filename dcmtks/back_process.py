# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 
"""
from time import sleep
import os
from sqlalchemy import and_
from configparser import ConfigParser
from datacenter import db, create_app
from datacenter.models import Tasks, AEDict, Patients
from dcmtks.pydcmtk import DcmTrans


def back_server():
    app = create_app()
    app.app_context().push()  # 在视图以外不加这句会报错

    CFG = ConfigParser()
    CFG.read('config.ini')
    server_ip = CFG["DCMTK"].get("server_ip")
    server_port = CFG["DCMTK"].get("server_port")
    client_port = CFG["DCMTK"].get("client_port")
    aec = CFG["DCMTK"].get("aec")
    aet = CFG["DCMTK"].get("aet")

    while True:
        # 队列中任务
        flag = 1  # 未置顶,task没有变化
        task = Tasks.query.filter(Tasks.status_id == 7).order_by(Tasks.priority.desc()).order_by(
            Tasks.timestamp).first()
        # 查询任务状态为待处理的优先级最高,同一优先级按时间排序
        if task:
            try:
                task.active = True
                db.session.commit()
                patients = Patients.query.filter(and_(Patients.task_id == task.id, Patients.status_id == 7)).all()
                transport_to = AEDict.query.filter_by(id=task.transport_id).first_or_404().ae_title
                if not task.series:
                    series_desc = None
                else:
                    series_desc = task.series
                output_dir = make_output_dir_for_dicom(task)
                # output_dir = os.path.join('downloads', task.researcher.username, task.folder_name, 'images')
                print(output_dir)
                dt = DcmTrans(server_ip=server_ip, server_port=server_port, aec=aec, aet=aet,
                              my_port=client_port, output_dir=output_dir)
                for i, patient in enumerate(patients):
                    # 实时查询当前任务是否被取消
                    # ratio = str((i+1) / len(patients) * 100)
                    # 如果任务状态为待处理则继续进行
                    if task.status_id == 7:  # 队列中
                        accession_no = patient.accession_no
                        try:
                            print(accession_no, transport_to)
                            if transport_to == 'DOWNLOAD':
                                dt.download_dcms(AccessionNumber=accession_no, SeriesDescription=series_desc)
                            else:
                                dt.move(AccessionNumber=accession_no, aem=transport_to, SeriesDescription=series_desc)
                            patient.status_id = 1  # 完成
                        except Exception as e:
                            print(e)
                            patient.err_message = str(e)[:70]
                            patient.status_id = 3  # 失败
                        db.session.commit()
                        if i != len(patients) - 1:
                            sleep(task.time_wait * 60)
                    elif task.status_id == 2:  # 任务被取消
                        patient.status_id = 2  # 取消

                    # 判断任务是否被切换,切换则跳出for循环
                    new_task = Tasks.query.filter(Tasks.status_id == 7).order_by(Tasks.priority.desc()).order_by(
                        Tasks.timestamp).first()
                    if (not new_task) or new_task.id != task.id:
                        task.active = False
                        db.session.commit()
                        flag = 0
                        break

                if flag and task.status_id == 7:
                    err_count = Patients.query.filter(
                        and_(Patients.task_id == task.id, Patients.status_id == 3)).count()
                    count = Patients.query.filter(Patients.task_id == task.id).count()
                    failed_percent = err_count / count * 100
                    if failed_percent == 100:
                        # print('任务失败')
                        task.status_id = 3  # 任务失败
                    elif failed_percent > 0:
                        task.status_id = 4  # 部分完成
                    elif failed_percent == 0:
                        task.status_id = 1  # 完成
                    else:
                        raise(Warning, 'Unexpected failed_percent:{}'.format(failed_percent))

            except Exception as e:
                print('未知错误', e)
                task.status_id = 5  # 未知错误
            task.active = False
            db.session.commit()

        sleep(10)



def make_output_dir_for_dicom(task):
    output_dir = os.path.join('downloads', task.researcher.username, 'data', task.folder_name, task.timestamp)
    return output_dir

# if __name__ == "__main__":
#     back_server()


