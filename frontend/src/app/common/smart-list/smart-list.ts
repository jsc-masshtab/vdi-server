/**
		(c) 2017 АО "НИИ "МАСШТАБ"
*/

import {
	Component,
	Input,
	Output,
	EventEmitter,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
	Directive,
	HostListener,
  ViewContainerRef,
  ComponentFactoryResolver,
  ViewChild
} from '@angular/core';

import {
	trigger,
	state,
	style,
	transition,
	animate,
} from '@angular/animations';

//import * as moment from 'moment';

//import { FactoryService } from '../../factory';
import { SmartListService } from './smart-list.service';

@Component({
	selector: 'smart-list',
	styleUrls: ['./smart-list.scss'],
	templateUrl: './smart-list.html',
	changeDetection: ChangeDetectionStrategy.OnPush,
}) export class SmartList {

	@Input() object: any = {};
	@Input() validators: any = {};
	@Input() showLines: any[] = [];
  @Output() actions = new EventEmitter<any>();

  @Input() parent: any;

  @Input() show_empty: boolean = false;

  @ViewChild('component', {read: ViewContainerRef}) component: ViewContainerRef;

  private hasProperty;

	constructor(
    //private factory: FactoryService,
    private local_service: SmartListService,
    private cdr: ChangeDetectorRef,
    private cfr: ComponentFactoryResolver) {}

	ngOnChanges() {
    this.update();
	}

	private action(action, data: any = null): void {
		if(action) {
			if(action == 'deep-smart-action') {
				this.actions.emit({
					action: data['action'],
          data : data['data']
				});
			} else {
				this.actions.emit({
					action: action,
          data : data
				});
			}
		}
	}

	private deepProperty(element, name) {
		let property = name.split('.');
		let entity = {...element};
		let is_set = true;

		for(let point = 0; point < property.length; point++){
			if(entity[property[point]]) {
				entity = entity[property[point]];
			} else {
				is_set = false;
			}
		}

		if(is_set) {
			return entity;
		} else {
			return '';
		}
	}

	private deepPropertyBoolean(element, name): string {
		let property = name.split('.');
		let entity = {...element};
		let is_set = true;

		for(let point = 0; point < property.length; point++){
			if(typeof(entity[property[point]]) == 'boolean') {
				entity = entity[property[point]];
			} else {
				is_set = false;
			}
		}

		if(is_set) {
			return entity;
		} else {
			return '';
		}
	}

	private update(): void {
    if(this.object || this.show_empty) {
      
      this.hasProperty = Object.keys(this.object).length;

      if(this.hasProperty || this.show_empty) {
        this.showLines = this.showLines.map((line: any) => {
          const data: any = {...line};
          const keys: any[] = line.key ? line.key.split(',') : [];

          if(line.type == 'array') {
            data['value'] = [];

            keys.forEach((key) => {
              let value = this.deepProperty(this.object, key);

              if(line.mapping) {
                value = value ? line.mapping(value) : '';
              }

              if(value) {
                data['value'] = data['value'].concat(value);

                data['value'].forEach(el => {
                  if(line.infocon) {
                    if(el[line.infocon.property] == line.infocon.condition) {
                      el['infocon'] = line.infocon.class || 'fa fa-circle';
                    }
                  }
                });
              }
            });

            if(line.toggle) {
              data['is_hidden'] = line['is_hidden'] === undefined ? true : line['is_hidden'];
            } else {
              if(data['value'].length) {
                data['is_hidden'] = false;
              } else {
                data['is_hidden'] = true;
              }
            }

            data['direction'] = line['direction'] ? line['direction'] : 'column';
            data['count'] = data['value'].length;

          } else if(line.type == 'list') {

            data['value'] = {};

            if(keys.length) {
              data['value'] = this.deepProperty(this.object, line.key);
            } else {
              data['value'] = {...this.object};
            }

            if(line.toggle) {
              data['is_hidden'] = line['is_hidden'] === undefined ? true : line['is_hidden'];
            }

            data['direction'] = line['direction'] ? line['direction'] : 'column';
            data['uncount'] = true;

          } else if(line.type == 'with_key' || line.type == 'without_key') {

            data['value'] = {};
            data['value'] = {...this.object[line.key]};
            data['direction'] = line['direction'] ? line['direction'] : 'row';
            data['uncount'] = true;
          }

          else if(line.type == 'object_group') {

            data['value'] = [];

            if(this.object[line.key] instanceof Object) {
              if(Object.keys(this.object[line.key]).length) {
                for (let item in this.object[line.key]) {
                  data['value'][item] = this.object[line.key][item];
                }
              }
            }
          }

          else if(line.type == 'list-array') {

            data['value'] = [];

            if(line.inject) {
              data['uncount'] = true;
            } else {
              if(keys) {
                data['value'] = [...this.deepProperty(this.object, line.key)];

              } else {
                data['value'] = [...this.object];
              }

              data['count'] = data['value'].length;
            }

            if(line.toggle) {
              this.init_toggle(line.list);
              data['is_hidden'] = line['is_hidden'] === undefined ? true : line['is_hidden'];
            }

            data['direction'] = line['direction'] ? line['direction'] : 'column';


          } else if(line.type == 'boolean') {

            data['value'] = "";

            keys.forEach((key, index) => {

              let value = this.deepPropertyBoolean(this.object, key);

              if(line.mapping) {
                data['value'] = line.mapping(value);
              } else {
                data['value'] = value ? 'вкл' : 'выкл';
              }
            });

            data['direction'] = line['direction'] ? line['direction'] : 'row';
            data['uncount'] = true;
          } else if(line.type == 'component') {

            data['no_header'] = true;
            data['direction'] = line['direction'] ? line['direction'] : 'column';

            this.componentFactory = this.cfr.resolveComponentFactory(line.component);
            this.componentData = line.inputs;
            this.componentInstance = line.instance;
      
          } else {

            data['value'] = '';

            keys.forEach((key, index) => {

              let value = this.deepProperty(this.object, key);

              if(line.mapping) {
                value = line.mapping(value,this.object);
              }

              data['value'] += value as string;

              if((keys.length - index) != 1) {
                data['value'] += ', ';
              }
            });


            data['direction'] = line['direction'] ? line['direction'] : 'row';
            data['uncount'] = true;
          }

          // if(line.format) {
          //   data['value'] = this.object[line.key] ? moment(this.object[line.key]).format(line.format) : '--';
          // }

          // if(line.format2) {
          //   keys.forEach((key) => {
          //     let value = +this.deepProperty(this.object, key);
          //     data['value'] = value ? moment.unix(value).utc().format(line.format2) : '--';
          //   });
          // }

          if(line.infocon) {
            if(this.deepProperty(this.object, line.infocon.property) == line.infocon.condition) {
              data['infocon'] = line.infocon.class || 'fa fa-circle';
            }
          }

          if(this.parent) {
            data['that'] = this.parent;
          }

          data['parent'] = this.object;
          data['buttons'] = line.buttons || [];

          if(line.header) {
            data['title'] = this.object[line.key];
          }

          return data;
        });
      }
    }
  }  
  
  componentFactory;
  componentData;
  componentRef;
  componentInstance;
  
  ngAfterViewInit() {

    if(this.componentFactory) {

      this.componentRef = this.component.createComponent(this.componentFactory);

      if(this.componentData) {
        Object.keys(this.componentData).forEach(input => {
          this.componentRef.instance[input] = this.componentData[input];
        });
      }

      if(this.componentInstance) {
        Object.keys(this.componentInstance).forEach((input) => {
          this.componentRef.instance[input] = this.deepProperty(this.object, this.componentInstance[input]);
        });
      }

      this.cdr.detectChanges();
    }
  }

  private init_toggle(list): void {
    list.forEach((line, ind) => {
      if(!line.header) {
        line['hide'] = line['hide'] === undefined ? true : line['hide'];
      } else {
        line['is_hidden'] = line['is_hidden'] === undefined ? true : line['is_hidden'];
      }
    });
  }

  private toggle_list(list): void {
    list.forEach((line, ind) => {
      if(!line.header) {
        line['hide'] = !line['hide'];
      } else {
        line['is_hidden'] = !line['is_hidden'];
      }
    });
  }

  private toggle(line): void {
    if(line['inject'] && line['is_hidden']) {

      let fields: any = null;

      if(line.inject['by']) {
        fields = {
          [line.inject['by']]: this.object[line.inject['by']]
        }
      }

      // this.local_service.emitAction(line['inject'], fields).subscribe((res) => {

      //   if(line.inject['property']) {
      //     line['value'] = [...res[line.inject['property']]];
      //   } else {
      //     line['value'] = [...res];
      //   }

      //   line['count'] = line['value'].length;
      //   line['uncount'] = false;

      //   this.cdr.detectChanges();
			// });
    }

    line['is_hidden'] = !line['is_hidden'];
  }

	public checkPermissions(line, action): boolean {
		let matchAction: number = Object.keys(line).indexOf(action);
		let matchPermissions: number = -1;
		if(line.permissions) {
			matchPermissions = Object.keys(line.permissions).indexOf(action);
		}

		if(matchAction != -1) {         // есть совпадение у action и ['propery'] в line
			if(!line.permissions) {
				return true;
			} else {
				if(this.object.permissions) {
					if(matchPermissions != -1) {
						if(this.object.permissions[line.permissions[action]]) {
							return true;
						} else {
							return false;
						}
					} else {
						return false;
					}
				} else {
					return true; // надо будет убрать.Есть line.permissions,но нет object.permissions,пока нет на бэке (для блочных хранилок)
				}
			}
		} else {
			return false;
		}
	}
}
