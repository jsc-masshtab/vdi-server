/**
  (c) 2017 АО "НИИ "МАСШТАБ"
*/

import {
    Component,
    Input,
    OnChanges,
    Output,
    EventEmitter,
    ChangeDetectionStrategy
} from '@angular/core';

import {
	trigger,
	state,
	style,
	transition,
	animate
} from '@angular/animations';

@Component({
    selector: 'ba-select',
    templateUrl: './baSelect.html',
    styleUrls: ['./baSelect.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
    animations: [
      trigger(
        'anim', [
          transition(':enter', [
            style({ opacity: 0 }),
            animate('50ms', style({ opacity: 1 }))
          ]),
          transition(':leave', [
            style({ opacity: 1 }),
            animate('50ms', style({ opacity: 0 }))
          ])
        ])
    ]
})

export class BaSelect {
    @Input() actionSelect: boolean = false;
    @Input() multySelect: boolean = false;
    @Input() filterSelect: boolean = false;
    @Input() addedSelect: boolean = false;
    @Input() disabled: boolean = false;
    @Input() selectShowBlock: boolean = false;
    @Input() invalidData: boolean = false;
    @Input() autoSelect: boolean = true;

    @Input() styleSelect: any = {};
    @Input() styleDropDown: any = {};

    @Input() inputData: any[] = [];
    @Input() defaultData: string = '- нет данных -';
    @Input() selectedBy: string = '';
    @Input() selectedByProp: string = '';
    @Input() itemType: string = 'string';

    @Output() outputData = new EventEmitter();
    @Output() outputFilter = new EventEmitter();

    private searchingData: any[] = [];
    private selectedData: any[] = [];
    private selectedShow: any[] = [];

    private isSelect: any[] = [];

    private init: boolean = false;
    private listTrigger: boolean = false;

    private openList(): void {
        if(!this.disabled) {
            if(this.filterSelect) {
                this.searchingData = [];
            }

            this.listTrigger = !this.listTrigger;
        }
    }

    private keydown(e) {
         if(e.keyCode == 13) {
            this.openList();
        } else if(e.keyCode != 9) {
            e.preventDefault();
        }
    }

    private keydownLi(e,data) {
        if(e.keyCode == 13) {
            this.sendData(data);
        } else if(e.keyCode != 9) {
            e.preventDefault();
        }
    }

    private sendAdd(e): void {
      if(e.value) {
        const data = {input: e.value, output: e.value};
        this.sendData(data, true);
      }
    }

    private sendData(data, add = false): void {
        if(!data.disabled) {

            if(this.multySelect) {
                const exists = this.isSelect.findIndex((selected: any) => selected.input === data.input);

                if(exists == -1) {
                    if(this.addedSelect && add) {
                      this.inputData.push(data);
                    }

                    this.isSelect.push(data);
                    if(this.itemType == 'number') {
                      this.selectedData.push(Number(data.output));
                    } else {
                      this.selectedData.push(data.output);
                    }
                    this.selectedShow.push({ title: data.input, icon: data.icon });

                    const ind = this.inputData.findIndex((inputdata: any) => inputdata.input === data.input);

                    if(ind != -1) {
                        this.inputData[ind]['selected'] = true;
                    }
                } else {
                    if(!add) {
                        this.isSelect.splice(exists,1);
                        this.selectedData.splice(exists,1);
                        this.selectedShow.splice(exists,1);

                        const ind = this.inputData.findIndex((inputdata: any) => inputdata.input === data.input);

                        if(ind != -1) {
                            this.inputData[ind]['selected'] = false;
                        }
                    }
                }

            } else {
                this.selectedData = [];
                this.selectedShow = [];
                this.selectedData.push(data.output);
                this.selectedShow.push({ title: data.input, icon: data.icon });
                this.listTrigger = false;
            }

            this.outputData.emit(this.selectedData);
        }
    }

    private initData(): void {
        this.selectedData = [];
        this.selectedShow = [];
        this.listTrigger = false;

        if(this.actionSelect) {
            this.selectedShow.push({title: this.defaultData});
        } else {
            let selected = false;
            let input_data: any[] = this.inputData;

            if (this.addedSelect) {
              this.multySelect = true;

              this.inputData = this.inputData.map((data)=> {
                if(data.input) {
                  data['selected'] = true;

                  return data;
                } else {
                  const option: any = {
                    input: data,
                    output: data,
                    selected: true
                  }

                  return option;
                }
              });
            }

            this.inputData.forEach((data)=> {

                if(this.selectedBy) {
                    if(this.selectedByProp) {
                        if(this.selectedBy == data.output[this.selectedByProp]) {

                            this.sendData(data);
    
                            if(data.disabled) {
                                this.selectedShow.push({title: data.input});
                            }
    
                            selected = true;
                        }
                    } else if(this.selectedBy == data.output) {

                        this.sendData(data);

                        if(data.disabled) {
                            this.selectedShow.push({title: data.input});
                        }

                        selected = true;
                    }
                } else if(data.selected) {

                    this.sendData(data);

                    if(data.disabled) {
                        this.selectedShow.push({title: data.input});
                    }

                    selected = true;
                }

            });

            if(input_data.length && !selected && this.autoSelect) {
                this.sendData(this.inputData[0]);
            }
        }
    }


    private searchData(value): void {
        this.searchingData = this.inputData.filter((item) => {
            return String(item.input).search(String(value)) != -1;
        });
    }

    ngOnChanges() {
        if(!this.invalidData) {
            this.initData();
        }
    }
}
