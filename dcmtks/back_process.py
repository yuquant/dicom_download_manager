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
# from flask import current_app
# from app import app


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
        app.config['BAR'] = {'title': '', 'percent': '0'}
        task = Tasks.query.filter(Tasks.status == 0).order_by(Tasks.priority.desc()).order_by(
            Tasks.timestamp).first()
        # 查询任务状态为待处理的优先级最高,同一优先级按时间排序
        if task:
            try:
                app.config['BAR'] = {'title': task.title, 'percent': '0'}
                task.active = True
                # db.session.add(task)
                db.session.commit()
                # patients = task.patients
                patients = Patients.query.filter(and_(Patients.task_id == task.id, Patients.status == 0)).all()
                transport_to = AEDict.query.filter_by(ae_id=task.transport_to).first_or_404().ae_title
                if not task.series:
                    series_desc = None
                else:
                    series_desc = task.series
                output_dir = os.path.join('downloads', task.folder_name, 'images')
                dt = DcmTrans(server_ip=server_ip, server_port=server_port, aec=aec, aet=aet,
                              my_port=client_port, output_dir=output_dir)
                failed_num = 0
                current_id = task.id
                for i, patient in enumerate(patients):
                    # 实时查询当前任务是否被取消
                    ratio = str((i+1) / len(patients) * 100)
                    app.config['BAR']['percent'] = ratio
                    print(ratio)
                    task = Tasks.query.filter(Tasks.id == current_id).first()
                    # 如果任务状态为待处理则继续进行
                    if task.status == 0:  # 任务待处理
                        accession_no = patient.accession_no
                        try:
                            print(accession_no, transport_to)
                            if transport_to == 'DOWNLOAD':
                                dt.download_dcms(AccessionNumber=accession_no, SeriesDescription=series_desc)
                            else:
                                dt.move(AccessionNumber=accession_no, aem=transport_to, SeriesDescription=series_desc)
                            patient.status = 1  # 完成
                        except Exception as e:
                            print(e)
                            patient.err_message = str(e)[:70]
                            patient.status = 3  # 失败
                            failed_num += 1
                        # db.session.add(patient)
                        db.session.commit()
                        if i != len(patients) - 1:
                            sleep(task.time_wait * 60)
                    elif task.status == 2:  # 任务被取消
                        patient.status = 2  # 取消
                        # db.session.add(patient)
                failed_percent = failed_num / len(patients)
                if task.status == 0:
                    if failed_percent == 1:
                        task.status = 3  # 任务失败
                    elif failed_percent > 0:
                        task.status = 4  # 部分完成
                    elif failed_percent == 0:
                        task.status = 1  # 完成
                    else:
                        raise(Warning, 'Unexpected failed_percent:{}'.format(failed_percent))
                task.active = False
                # db.session.add(task)
                db.session.commit()

            except Exception as e:
                print(e)
                task.status = 5  # 未知错误
                # db.session.add(task)
                db.session.commit()
                sleep(10)
        sleep(10)
# if __name__ == "__main__":
#     back_server()
