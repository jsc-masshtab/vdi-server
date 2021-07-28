
export interface IParams {
    spin: boolean;
    nameSort?: string;
}

export interface IEditFormObj {
    title: string,
    property: string,
    type: string | {},
    formEdit: [{
        header: string,
        tag: 'input',
        type: 'text' | 'number' | 'checkbox',
        fieldName: string,
        fieldValue: string | number | boolean
    }],
    edit: 'openEditForm',  
}