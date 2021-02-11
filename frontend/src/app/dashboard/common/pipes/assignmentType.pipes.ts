
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'assignmentType' })
export class AssignmentTypePipe implements PipeTransform {

    constructor() { }

    transform(assignmentType) {
        let translateAssignmentType = '';
        if (assignmentType === 'backup') {
            translateAssignmentType = 'Резервная копия';
        } else if (assignmentType === 'node_backup_os') {
            translateAssignmentType = 'Резервная копия сервера';
        } else if (assignmentType === 'backup_ova') {
            translateAssignmentType = 'Резервная копия OVA';
        } else if (assignmentType === 'backup_os') {
            translateAssignmentType = 'Резервная копия ОС';
        } else if (assignmentType === 'node_profile') {
            translateAssignmentType = 'Файл профиль';
        } else if (assignmentType === 'image_qcow2') {
            translateAssignmentType = 'Образ qcow2';
        } else if (assignmentType === 'image_vmdk') {
            translateAssignmentType = 'Образ vmdk';
        } else if (assignmentType === 'image_raw') {
            translateAssignmentType = 'Образ raw';
        } else if (assignmentType === 'domain_ovf') {
            translateAssignmentType = 'OVF';
        } else if (assignmentType === 'archive') {
            translateAssignmentType = 'Архив';
        } else if (assignmentType === 'domain_xml') {
            translateAssignmentType = 'XML';
        } else if (assignmentType === 'xml_unsupported') {
            translateAssignmentType = 'XML не поддерживается';
        } else if (assignmentType === 'ovf_unsupported') {
            translateAssignmentType = 'OVF не поддерживается';
        } else {
            translateAssignmentType = assignmentType;
        }
        return translateAssignmentType;
    }
}
