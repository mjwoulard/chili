﻿using System;
using System.Collections.Generic;

namespace Usa.chili.Domain
{
    public partial class ContactInfo
    {
        public short Id { get; set; }
        public string StationKey { get; set; }
        public string Role { get; set; }
        public string Type { get; set; }
        public short PersonId { get; set; }
    }
}
